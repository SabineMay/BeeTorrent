from enum import Enum
import hashlib

# we should never get overlapping blocks because we control the (idx, begin) parameters in request
# all the uploader has to do is respond with the number of bytes we requested
class PieceList: 
    
    class Status(Enum):
        REQUESTED = -1
        READY = 0
        RECEIVED = 1
        
        UNRESOLVED = 2
        RESOLVED = 3

    def __init__(self, _num_pieces, _piece_length, _blocks_per_piece, _block_length, output_file, hashes): 
        self.pieces = [PieceList.Status.UNRESOLVED] * _num_pieces
        self.blocks = [PieceList.Status.RESOLVED] * _blocks_per_piece * _num_pieces
        
        self.num_pieces = _num_pieces
        self.piece_length = _piece_length
        
        self.blocks_per_piece = _blocks_per_piece
        self.block_length = _block_length
        
        self.output_file = output_file
        self.hashes = hashes
    
    def request(self, piece_idx, block_idx):
        self.blocks[piece_idx + block_idx] = PieceList.Status.REQUESTED
    
    def ready(self, piece_idx, block_idx):
        self.blocks[piece_idx + block_idx] = PieceList.Status.READY
    
    def receive(self, piece_idx, block_idx):
        self.blocks[piece_idx + block_idx] = PieceList.Status.RECEIVED
        self.attempt_resolve(piece_idx)
        
    def is_requested(self, piece_idx, block_idx):
        if (self.blocks[piece_idx + block_idx] == PieceList.Status.REQUESTED):
            return True
        return False
    
    def is_ready(self, piece_idx, block_idx):
        if (self.blocks[piece_idx + block_idx] == PieceList.Status.READY):
            return True
        return False
        
    def is_received(self, piece_idx, block_idx):
        if (self.blocks[piece_idx + block_idx] == PieceList.Status.RECEIVED):
            return True
        return False
    
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
    
    def is_resolved(self, piece_idx):
        if (self.pieces[piece_idx] == PieceList.Status.RESOLVED):
            return True
        return False
    
    