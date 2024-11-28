import selectors
import socket 
import sys
from Bee import Bee
from bcoding import bencode, bdecode

def main():
    ip = "127.0.0.1" # get visible IP of this machine
    port = 1025 # port = int(sys.argv[2]) # user-set port on which to accept peer connections
    
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.bind((ip, port))
    listen_sock.listen(10) # listen to a max of 10 queued connections
    
    # tracker_sock, tracker_addr = listen_sock.accept()
    # print("Tracker located at " + tracker_addr[0] + ":" + tracker_addr[1]\n)
    # tracker_sock.send(HTTP get request) # send request to tracker
    # bdata = tracker_sock.recv() # receive bencoded tracker response
    metadata = {"peers":[{"peer id": 5, "ip": "127.0.0.1", "port": 1024}]} # metadata = bdecode(bdata)
    swarm = list()
    for peer in metadata["peers"]:
        newbie = Bee()
        newbie.set_id(peer["peer id"], peer["ip"], peer["port"]) # potential problem: does tracker return ip as a dotted decimal string or an integer?
        newbie.set_client_sock(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        try:
            newbie.client_sock.connect(newbie.addr) 
        except: 
            print("client_sock connection refused\n")
        swarm.append(newbie)
        
    # tracker_sock.send(info about me) # send info about myself to tracker
    for bee in swarm: 
        print(bee.to_string())

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