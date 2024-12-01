from enum import Enum

class PieceList: 
    
    class Status(Enum):
        REQUESTED = -1
        READY = 0
        RESOLVED = 1

    def __init__(self, _num_pieces, _piece_length): 
        self.pieces = [PieceList.Status.READY] * _num_pieces
        self.num_pieces = _num_pieces
        self.piece_length = _piece_length
    
    def request(self, pos):
        self.pieces[pos] = PieceList.Status.REQUESTED
    
    def ready(self, pos):
        self.pieces[pos] = PieceList.Status.READY
    
    def resolve(self, pos):
        self.pieces[pos] = PieceList.Status.RESOLVED
        
    def is_requested(self, pos):
        if (self.pieces[pos] == PieceList.Status.REQUESTED):
            return True
        return False
    
    def is_ready(self, pos):
        if (self.pieces[pos] == PieceList.Status.READY):
            return True
        return False
        
    def is_resolved(self, pos):
        if (self.pieces[pos] == PieceList.Status.RESOLVED):
            return True
        return False