from enum import Enum
import hashlib

"""
Class that tracks which pieces we have hash-verified, and which blocks we have received.

Pieces are uniform divisions of the output file, except for the last piece in the file which
may be shorter. Piece length is dictated by the torrent file 

Blocks are uniform subdivisions of pieces, except for the last block in every piece which
may be shorter. We set our own block length (and tell peers about it by using the length variable
in request messages). 
"""
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
        self.blocks = [PieceList.Status.RESOLVED] * _blocks_per_piece * _num_pieces
        
        self.num_pieces = _num_pieces
        self.piece_length = _piece_length
        
        self.blocks_per_piece = _blocks_per_piece
        self.block_length = _block_length
        
        self.output_file = output_file
        self.hashes = hashes
    
    # Update status of block to REQUESTED
    def request(self, piece_idx, block_idx):
        self.blocks[piece_idx * _blocks_per_piece + block_idx] = PieceList.Status.REQUESTED
    
    # Update status of block to READY
    def ready(self, piece_idx, block_idx):
        self.blocks[piece_idx * _blocks_per_piece + block_idx] = PieceList.Status.READY
    
    # Update status of bock to RECEIVED, and attempt to 
    # resolve the piece that the block is a part of
    def receive(self, piece_idx, block_idx):
        self.blocks[piece_idx * _blocks_per_piece + block_idx] = PieceList.Status.RECEIVED
        self.attempt_resolve(piece_idx)
    
    # Returns True if status of block is REQUESTED
    def is_requested(self, piece_idx, block_idx):
        if (self.blocks[piece_idx * _blocks_per_piece + block_idx] == PieceList.Status.REQUESTED):
            return True
        return False
    
    # Returns True if status of block is READY
    def is_ready(self, piece_idx, block_idx):
        if (self.blocks[piece_idx * _blocks_per_piece + block_idx] == PieceList.Status.READY):
            return True
        return False
    
    # Returns True if status of block is RECEIVED
    def is_received(self, piece_idx, block_idx):
        if (self.blocks[piece_idx * _blocks_per_piece + block_idx] == PieceList.Status.RECEIVED):
            return True
        return False
    
    # Checks to see if all blocks in piece have been 
    # received. If yes, checks the hash of the entire
    # piece. If the hash is correct, marks the piece
    # as RESOLVED. Otherwise, resets all the blocks within
    # the piece to READY
    def attempt_resolve(self, piece_idx):
        for block_idx in range(self.blocks_per_piece):
            if (not self.is_received(piece_idx, block_idx)):
                return False
            
        self.output_file.seek((piece_idx * self.piece_length), 0)
        if (hashlib.sha1(self.output_file.read(self.piece_length)) == self.hashes[piece_idx]):
            return True
        
        for block_idx in range(self.blocks_per_piece):
            self.ready(piece_idx, block_idx)
            
        return False
    
    # Returns True if status of piece is RESOLVED
    def is_resolved(self, piece_idx):
        if (self.pieces[piece_idx] == PieceList.Status.RESOLVED):
            return True
        return False
    
    