import time

class Bee: # part of the swarm
    def __init__(self):
        self.peerid = None
        self.addr = (None, None)
        self.clock = time.monotonic()
        self.sock = None
    
    def __eq__(self, other):
        if (self.addr == other.addr): # potential issue: is this the correct way to check for tuple equality
            return True
        
        return False

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
    

