import time
from bitstring import Bits, BitArray, BitStream, pack
from Request import Request

class Bee: # part of the swarm
    def __init__(self, num_pieces):
        self.peerid = None
        self.addr = (None, None)
        self.clock = time.monotonic()
        self.sock = None
        
        self.peer_interested = False
        self.peer_choked = True
        self.me_interested = False
        self.me_choked = True
        
        self.bitfield = BitArray(length=num_pieces)
        
        self.request_queue = list()
        self.max_requests = 5
        self.num_requests = 0
    
    def __eq__(self, other):
        if (self.addr == other.addr): # potential issue: is this the correct way to check for tuple equality
            return True
        
        return False
    
    def queue_request(self, request: Request):
        if (request in self.request_queue):
            for r in self.request_queue: 
                if r == request:
                    r.reset_clock()
                    break
                
        elif (self.num_requests == self.max_requests):
            self.request_queue.pop(-1)
            self.num_requests -= 1
        
        self.request_queue.append(Request)
        self.num_requests += 1
    
    def cancel_request(self, idx, begin, length):
        self.request_queue.remove((idx, begin, length))
        self.num_requests += 1

    # takes strings for ip, int for port
    def set_id(self, peerid, ip, port):
        self.peerid = peerid 
        self.addr = (ip, port)
        
    def reset_clock(self):
        self.clock = time.monotonic()

    def get_time_elapsed(self):
        return self.clock - time.monotonic()
    
    def to_string(self): 
        return "Bee: [peer_id: " + str(self.peerid) + ", addr: " + str(self.addr[0]) + ":" + str(self.addr[1]) + ", clock: " + str(self.clock) + "]\n"
    

