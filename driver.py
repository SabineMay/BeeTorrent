import selectors
import socket 
import sys
from Bee import Bee
from torrent_get_requests import get_info_from_tracker_specified_in_file
import time

from bcoding import bencode, bdecode

def main():
    sel = selectors.DefaultSelector() # only holds listen_sock, bee.server_sock's, and tracker_sock
    
    ip = "127.0.0.1" # get visible IP of this machine
    port = 1025 # port = int(sys.argv[2]) # user-set port on which to accept peer connections
    
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.bind((ip, port))
    listen_sock.listen(5) # listen to a max of 5 queued connections, non blocking
    
    sel.register(listen_sock, selectors.EVENT_READ)
    
    # tracker_addr = from bencoded dict
    # print("Tracker located at " + tracker_addr[0] + ":" + tracker_addr[1]\n)
    # tracker_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # tracker_sock.connect(tracker_addr)
    
    # tracker_sock.send(HTTP get request) # send request to tracker with info about the socket we're listening on 
    # bdata = tracker_sock.recv() # receive bencoded tracker response

    ((tracker_domain, tracker_port), metadata) = get_info_from_tracker_specified_in_file("tor-file-examples/kali-linux.torrent", 6881, event='started')   

    # metadata = {"interval": 100, "peers":[{"peer id": 5, "ip": "127.0.0.1", "port": 1024}]} # metadata = bdecode(bdata)
    
    if ("failure reason" in metadata): 
        print("Failed to get metadata from tracker: " + metadata["failure reason"] + "\n")
        exit()
    
    interval = metadata["interval"]
    peers = metadata["peers"]
    swarm: list[Bee] = list()
    for peer in peers:
        newbie = Bee()
        newbie.set_id(peer["peer id"], peer["ip"], peer["port"]) # potential problem: does tracker return ip as a dotted decimal string or an integer?
        
        try:
            newbie.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            newbie.client_sock.connect(newbie.addr) 
            # do handshake
            # delete peer and close socket if handshake failed
        except: 
            print("initial socket connection to peer refused\n")
            
        swarm.append(newbie)
        
    # all peers start off choked and us not interested
    for bee in swarm: 
        # bee.sock.send(choke)
        # bee.sock.send(not interested)
        print(bee.to_string())
        
    auction_clock = time.monotonic() # 10 seconds should elapse before every non-optimistic choke/unchoke
    charity_clock = time.monotonic() # 30 seconds should elapse before every optimistic unchokex
    tracker_clock = time.monotonic() # interval seconds should elapse before we update tracker with our status and how much we've downloaded/uploaded
    
    while(True):
        events = sel.select(timeout = 5) # potential issue: need to adjust timeout based on how much time left on auction/tracker/charity clocks
        
        for key, mask in events: 
            
            # getting a connect() message from a peer
            if (key.fd == listen_sock): 
                addr, sock = key.fd.accept()
            
                curr = None
                
                for bee in swarm: 
                    if (bee.remote_addr == addr): # potential problem: is this the right way to check equality of tuples?
                        print("Peer tried to establish duplicate connection with me")
                        sock.close()
                        bee.reset_clock()
                        curr = bee
                        break
                    
                if (curr == None):
                    print("Got a message from an peer that we didn't see in the tracker, attempting to handshake\n")
                    # do handhsake
                    # delete peer and close socket if handshake failed
                    sel.register(sock, selectors.EVENT_READ)
                    bee.sock = sock
                    
            
            # getting a message from a peer on an already-established socket
            else: 
                curr = None
                for bee in swarm: 
                    if (key.fd == bee.server_sock): # potential problem: is this the right way to check equality of tuples?
                        bee.reset_clock()
                        curr = bee
                        break
                
                if (curr == None):
                    print("Couldn't find peer assocated with selected socket in swarm")
                
                else: 
                    pass # handle_msg(curr.client_sock, key.fobject) <-- in another .py module
            
                # for handle_message: 
                # if message is us getting pieces, going to need a datastructure to keep track of top 4 uploaders for future unchoking
                # if message is someone else requesting pieces, going to need a datastructure to keep track of current unchoked nodes to which we will respond
                # this data structure needs to be visible to the auction clock and charity clock logic blocks below
                
        for bee in swarm: 
            if (bee.get_time_elapsed > 120): # 2 minutes since last message
                sel.unregister(bee.server_sock)
                swarm.remove(bee)
                
        curr_time = time.monotonic()

        if (curr_time - auction_clock >= 10):
            # recalculate top 4 interested uploaders 
            auction_clock = time.monotonic() # reset clock

        if (curr_time - charity_clock >= 30):
            # optimistically unchoke a new person 
            charity_clock = time.monotonic() # reset clock
        

    # BRAINSTORM:
    # get list of all peer ips from tracker
    # maintain data structure to associate peerids with IP:port pairs
        # do peerids get given by tracker or not? 
            # yes, peerids are chosen by the peers themselves, and we verify they are 
            # who they say they are during the handshaek
            # we only need to generate our own peerid --> just use rand()? 
        # potential problem: peerids need to be escaped
    # interval = value gotten from tracker that tells you how often to rerequest peices 
    # send choke and not interested to all peers
        # question: we need to keep interested/not interested up to date at all times -> does this mean we need to 
        # send periodic "still not interested" messages or do we only update when there is a change in our interest state? 
    #

    # need to maintain who is a "new" connection so that we can give them 3x greater probability of being optimistically unchoked 
        # should we define newness by timestamp or some other combination of interest/unchoke historical states? 
    # need to maintain keepalive timestamps/monotonic clock counters that we reset upon receipt of a keepalive message (or any other message probably)

    # every ten seconds loop: 
        # decide who to non-optimistcally unchoke, and choke everyone else (besides someone who si already optimistcally unchoked)

    # question: why do nodes need to know if they're choked or not --> why isn't it just something that I need to know? 

    # every 30 seconds loop
        # change who is optimistically unchoked 



if __name__=="__main__":
    main()