import time
from Request import Request

"""
Class containing information about each peer.
"""

class Bee: # part of the swarm
    def __init__(self, num_pieces):
        self.peerid = None
        self.addr = (None, None)
        self.clock = time.monotonic()
        
        # Either the socket that we connected to the peer with, or the socket
        # that listen() created after the peer connected to us
        # Will almost certaintly be the former given that we're behind a firwall
        self.sock = None
        
        self.peer_interested = False
        self.peer_choked = True
        self.me_interested = False
        self.me_choked = True
        
        # number of blocks the peer has succesfully uploaded to me in this period
        self.blocks_uploaded = 0
        
        # pieces that the peer has, used to determine what I should request
        self.bitfield = [False] * num_pieces
        # the bitfield has been initialized based on a bitfield or have message
        self.bitfield_initialized = False
        
        # blocks that the peer wants, updated when handling requests and used when unchoking
        self.request_queue = list()
        self.max_requests = 5
        self.num_requests = 0

        # pending requests that we sent to the peer
        self.num_pending_requests_sent = 0
    
    def __eq__(self, other):
        if (other != None and self.addr == other.addr): # potential issue: is this the correct way to check for tuple equality
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
        self.num_requests -= 1

    # takes strings for ip, int for port
    def set_id(self, peerid, ip, port):
        self.peerid = peerid 
        self.addr = (ip, port)
        
    def reset_clock(self):
        self.clock = time.monotonic()

    def get_time_elapsed(self):
        return self.clock - time.monotonic()
    
    def set_bitfield_at_index(self, piece_idx, value):
        self.bitfield[piece_idx] = value
        self.bitfield_initialized = True
    
    def update_bitfield_from_received_bitfield(self, bitfield):
        i = 0

        # get the nth bit in a given byte and return True if its 1 and False if its 0
        boolean_from_bit = lambda byte, n: True if ((byte >> n) & 0x1 == 1) else False

        # loop through the bytes and adjust the array accordingly
        for byte in bitfield:
            j = 0
            while j < 8:
                if (i * 8) + j < len(self.bitfield):
                    self.bitfield[(i * 8) + j] = boolean_from_bit(byte, (7 - j))
                else:
                    break
                j += 1
            i += 1
        
        self.bitfield_initialized = True
    
    def to_string(self): 
        return "Bee: [peer_id: " + str(self.peerid) + ", addr: " + str(self.addr[0]) + ":" + str(self.addr[1]) + ", clock: " + str(self.clock) + "]"
    

