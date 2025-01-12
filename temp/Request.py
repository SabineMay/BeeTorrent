import time

class Request:
    def __init__(self, _idx, _begin, _length):
        self.idx = _idx
        self.begin = _begin
        self.length = _length
        self.clock = time.monotonic()
    
    def __eq__(self, other):
        if (self.idx == other.idx and self.begin == other.begin and self.length == other.length):
            return True
        
        return False
        
    def reset_clock(self):
        self.clock = time.monotonic()

    def get_time_elapsed(self):
        return self.clock - time.monotonic()