import time

class Bee: # part of the swarm
    def __init__(self):
        self.peerid = -1
        self.addr = (-1, -1)
        self.clock = time.monotonic()
        self.client_sock = -1
        self.server_sock = -1
    
    def set_id(self, _peerid, _remote_ip, _remote_port):
        self.peerid = _peerid 
        self.addr = (_remote_ip, _remote_port)

    def set_client_sock(self, _client_sock):
        self.client_sock = _client_sock
        
    def set_server_sock(self, _server_sock):
        self.server_sock = _server_sock
    
    def reset_clock(self):
        self.clock = time.monotonic()

    def get_time_elapsed(self):
        return self.clock - time.monotonic()
    
    def to_string(self): 
        return "Bee " + str(self.peerid) + ": [addr: " + str(self.addr[0]) + ":" + str(self.addr[1]) + ", clock: " + str(self.clock) + "]\n"
    

