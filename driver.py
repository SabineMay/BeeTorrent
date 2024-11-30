import selectors
import socket 
import sys
from Bee import Bee
from get_info_from_tracker import *
import time
import random
from handshake import *
from errors import *

from bcoding import bencode, bdecode

TORRENT_FILE_PATH = 'tor-file-examples/cosmos-laundromat.torrent'

def main():
    initiate_logs()

    # peerid communicated to tracker and to peers during handshake
    azureus = ("-MD0417-").encode("utf-8")
    random_bytes = random.randbytes(12)
    myid = azureus + random_bytes
    print("My id is " + str(myid) + "\n")

    # info_hash for use in handshake
    torfile = open(TORRENT_FILE_PATH, 'rb')
    tde = bdecode(torfile)
    h = hashlib.sha1()

    h.update(bencode(tde['info']))

    info_hash = h.digest()

    
    # used to poll over peer sockets 
    sel = selectors.DefaultSelector() 
    
    # commented out below because we don't need it (don't need to explicitly tell the tracker our ip)

    # get visible IP of this machine - requires requests library (or manual conversation with an external host);
    # see https://stackoverflow.com/questions/17309288/importerror-no-module-named-requests;
    # probably not actually necessary for this assigment - the tracker determines and advertises
    # your ip via the socket connection you have with it;
    # this also might not work in docker or VM
    # ip = requests.get('https://checkip.amazonaws.com').text.strip() 
    # print("my ip is: " + str(ip))
    
    # port on which I listen for new connections;
    # communicated to tracker 
    port = 1027 # port = int(sys.argv[1]) # user-set port on which to accept peer connections
    
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.bind(("0.0.0.0", port)) 
    listen_sock.listen(5) # listen to a max of 5 queued connections, standard for bittorrent
    
    sel.register(listen_sock, selectors.EVENT_READ)

    metadata = None
    
    try:
        metadata = get_info_from_tracker_specified_in_file(TORRENT_FILE_PATH, port, myid, event='started')
    except Exception as e:
        log_error(Exception("Failed when getting information from tracker: " + str(e)))
        print("Getting information from tracker did not work with error " + str(e))
        print("Make sure the tracker is up and running")
        exit()
    
    # peers (in metadata) can either be a dictionary or a bytestring in the following format:
    # 4 bytes for ip address of peer 1, 2 bytes for port of peer 1, 4 bytes for ip of peer 2, 2 bytes for port
    # of peer 2, etc.
    # metadata = {"interval": 100, "peers":[{"peer id": 5, "ip": "127.0.0.1", "port": 1024}]}
    
    if ("failure reason" in metadata): 
        print("Failed to get metadata from tracker: " + metadata["failure reason"] + "\n")
        exit()
    
    interval = metadata["interval"]
    peers = metadata["peers"]
    print("Metadata is: " + str(metadata) + "\n")
    swarm: list[Bee] = list()
    compact = False
    
    if (not isinstance(peers, list)):
        # tracker is in compact mode
        # peers are one large byte string, with no peer id furnished
        compact = True
        peers = [peers[i:i+6] for i in range(0, len(peers), 6)]
    
    print(peers)
    for peer in peers:
        newbie = Bee()
        
        if (compact):
            newbie.set_id(None, extract_ip(peer), extract_port(peer))
        else: 
            newbie.set_id(peer["peer id"], peer["ip"], peer["port"]) # potential problem: does tracker return ip as a dotted decimal string or an integer?
        
        newbie.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        newbie.sock.settimeout(1)
        
        try:
            newbie.sock.connect(newbie.addr) 
            # do handshake
            # close socket if handshake failed
        except Exception as e: 
            print("Could not connect to peer " + str(newbie.addr) + " (" + (str(e)) + ")\n")
            log_error(Exception("Could not connect to peer " + str(newbie.addr) + " (" + (str(e)) + ")"))
            newbie.sock.close()
        else: 
            # recommended to set non blocking for use with selectors, so in case of edge cases the program won't hang
            # kept the socket blocking durring connect() so that we know if connect failures are from 
            # server not responding (timeout) or server actively rejecting us
            try:
                send_handshake(newbie.sock, info_hash, myid)
                recv_handshake(newbie.sock)
                print("Sucesfully connected to peer " + str(newbie.addr) + "\n")
                newbie.sock.setblocking(False) 
                swarm.append(newbie)
            except Exception as e:
                print("Failed to handshake with peer " + str(newbie.addr) + "\n")
                log_error(Exception("Failed handshake with " + str(newbie.addr) +  ": " + str(e)))
    
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
                    if (bee.addr == addr): # potential problem: is this the right way to check equality of tuples?
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
                    if (key.fd == bee.sock): # potential problem: is this the right way to check equality of tuples?
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
            if (bee.get_time_elapsed() > 120): # 2 minutes since last message
                sel.unregister(bee.sock)
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
