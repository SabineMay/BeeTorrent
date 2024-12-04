from enum import Enum
import hashlib
import random
import time

"""
Class that tracks which pieces we have hash-verified, and which blocks we have received.

Pieces are uniform divisions of the output file, except for the last piece in the file which
may be shorter. Piece length is dictated by the torrent file 

Blocks are uniform subdivisions of pieces, except for the last block in every piece which
may be shorter. We set our own block length (and tell peers about it by using the length variable
in request messages). 
"""
# 10 second wait to rerequest a piece
TIMEOUT = 10

class PieceList: 
    
    class Status(Enum):
        REQUESTED = -1
        READY = 0
        RECEIVED = 1
        
        UNRESOLVED = 2
        RESOLVED = 3

    def __init__(self, _num_pieces, _piece_length, _blocks_per_piece, _block_length, output_file, hashes): 
        
        # keeps track of which pieces have been hash-verified (RESOLVED) and not (UNRESOLVED)
        self.pieces = [PieceList.Status.UNRESOLVED] * _num_pieces
        
        # keeps track of which blocks still need to be requested (READY), have been requested (REQUESTED), and were succesfully received (RECEIVED)
        self.blocks = [PieceList.Status.READY] * _blocks_per_piece * _num_pieces
        
        self.num_pieces = _num_pieces
        self.piece_length = _piece_length
        
        self.blocks_per_piece = _blocks_per_piece
        self.block_length = _block_length
        
        self.output_file = output_file
        self.hashes = hashes

        self.request_times = {}

        self.num_pieces_resolved = 0
        
        self.last_block_length = _block_length

        self.last_piece_num_blocks = _blocks_per_piece

        self.last_piece_length = self.piece_length
    
    # Update status of block to REQUESTED
    def request(self, piece_idx, block_idx):
        self.blocks[piece_idx * self.blocks_per_piece + block_idx] = PieceList.Status.REQUESTED
        self.request_times[piece_idx * self.blocks_per_piece + block_idx] = time.time()
    
    # Update status of block to READY
    def ready(self, piece_idx, block_idx):
        self.blocks[piece_idx * self.blocks_per_piece + block_idx] = PieceList.Status.READY

    def set_timedout_requests_to_ready(self):
        curr = time.time()
        timedout = []
        for index in self.request_times:
            if (curr - self.request_times[index]) > TIMEOUT:
                self.blocks[index] = PieceList.Status.READY
                timedout.append(index)
        
        for index in timedout:
            self.request_times.pop(index, -1)
    
    # last piece might have less than normal amount of blocks
    def downsize_last_piece(self, output_file_length):
        if output_file_length < (self.num_pieces * self.piece_length):
            last_piece_length = output_file_length - ((self.num_pieces - 1) * self.piece_length)
            self.last_piece_length = last_piece_length
            self.last_block_length = last_piece_length % self.block_length
            size_of_last_piece_minus_last_block = last_piece_length - self.last_block_length
            self.last_piece_num_blocks = (size_of_last_piece_minus_last_block // self.block_length) + 1

            if (self.last_piece_num_blocks != self.blocks_per_piece):
                del self.blocks[-(self.blocks_per_piece - self.last_piece_num_blocks):]

            
    # Update status of bock to RECEIVED, and attempt to 
    # resolve the piece that the block is a part of
    def receive(self, piece_idx, block_idx):
        self.blocks[piece_idx * self.blocks_per_piece + block_idx] = PieceList.Status.RECEIVED
        self.request_times.pop(piece_idx * self.blocks_per_piece + block_idx, -1)
        print("received: " + str(piece_idx) + ", " + str(block_idx))
        self.attempt_resolve(piece_idx)
    
    # Returns True if status of block is REQUESTED
    def is_requested(self, piece_idx, block_idx):
        if (self.blocks[piece_idx * self.blocks_per_piece + block_idx] == PieceList.Status.REQUESTED):
            return True
        return False
    
    # Returns True if status of block is READY
    def is_ready(self, piece_idx, block_idx):
        if (self.blocks[piece_idx * self.blocks_per_piece + block_idx] == PieceList.Status.READY):
            return True
        return False
    
    # Returns True if status of block is RECEIVED
    def is_received(self, piece_idx, block_idx):
        if (self.blocks[piece_idx * self.blocks_per_piece + block_idx] == PieceList.Status.RECEIVED):
            return True
        return False
    
    # Checks to see if all blocks in piece have been 
    # received. If yes, checks the hash of the entire
    # piece. If the hash is correct, marks the piece
    # as RESOLVED. Otherwise, resets all the blocks within
    # the piece to READY
    def attempt_resolve(self, piece_idx):
        num_blocks_in_piece = self.blocks_per_piece

        if piece_idx == self.num_pieces - 1:
            num_blocks_in_piece = self.last_piece_num_blocks

        for block_idx in range(num_blocks_in_piece):
            if (not self.is_received(piece_idx, block_idx)):
                return False
            
        self.output_file.seek((piece_idx * self.piece_length), 0)

        h = hashlib.sha1()

        piece_length = self.piece_length

        if piece_idx == self.num_pieces - 1:
            piece_length = self.last_piece_length

        h.update(self.output_file.read(piece_length))

        if (h.digest() == self.hashes[piece_idx]):
            self.pieces[piece_idx] = PieceList.Status.RESOLVED
            self.num_pieces_resolved += 1
            return True
        
        for block_idx in range(num_blocks_in_piece):
            self.ready(piece_idx, block_idx)
            
        return False

    # takes a bees bitfield and checks if any of the blocks in any of the pieces that bee has
    # are blocks that we haven't received yet
    def check_interest(self, bitfield):
        piece_idx = 0
        for piece in bitfield:
            block_idx = 0
            if piece == True:
                while block_idx < self.blocks_per_piece and piece_idx * self.blocks_per_piece + block_idx < len(self.blocks):
                    if self.blocks[piece_idx * self.blocks_per_piece + block_idx] != PieceList.Status.RECEIVED:
                        return True
                    block_idx += 1
            piece_idx += 1

    # Returns True if status of piece is RESOLVED
    def is_resolved(self, piece_idx):
        if (self.pieces[piece_idx] == PieceList.Status.RESOLVED):
            return True
        return False

    def piece_has_blocks_to_be_requested(self, piece_idx):
        block_idx = 0
        while block_idx < self.blocks_per_piece and piece_idx * self.blocks_per_piece + block_idx < len(self.blocks):
            if self.blocks[piece_idx * self.blocks_per_piece + block_idx] == PieceList.Status.READY:
                return True
            block_idx += 1
        return False

    
    def get_needed_block_for_piece(self, piece_idx):
        if (self.is_resolved(piece_idx)):
            return -1
        else:
            i = 0
            while i < self.blocks_per_piece:
                if (self.blocks[(piece_idx * self.blocks_per_piece) + i] != PieceList.Status.RECEIVED) and (self.blocks[(piece_idx * self.blocks_per_piece) + i] != PieceList.Status.REQUESTED):
                    return i
                i += 1
            # i = 0
            # while i < self.blocks_per_piece:
            #     if (self.blocks[(piece_idx * self.blocks_per_piece) + i] != PieceList.Status.RECEIVED):
            #         return i
            #     i += 1
        
        return -1


    
    