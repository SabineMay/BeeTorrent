import time

class Bee: # part of the swarm
    def __init__(self):
        self.peerid = -1
        self.remote_addr = (-1, -1)
        self.clock = time.monotonic()
        self.client_sock = -1
        self.server_sock = -1
    
    def __eq__(self, other):
        if (self.remote_addr == other.remote_addr): # potential issue: is this the correct way to check for tuple equality
            return True
        
        return False

    
    def set_id(self, _peerid, _remote_ip, _remote_port):
        self.peerid = _peerid 
        self.remote_addr = (_remote_ip, _remote_port)
        
    def reset_clock(self):
        self.clock = time.monotonic()

    def get_time_elapsed(self):
        return self.clock - time.monotonic()
    
    def to_string(self): 
        return "Bee " + str(self.peerid) + ": [addr: " + str(self.addr[0]) + ":" + str(self.addr[1]) + ", clock: " + str(self.clock) + "]\n"
    

