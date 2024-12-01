import selectors
import socket 
import sys
from Bee import Bee
from get_info_from_tracker import *
import time
import requests
import random
from construct_messages import *
from handle_messages import *
import math
from PieceList import PieceList

from bcoding import bencode, bdecode


def main():
    # peerid communicated to tracker and to peers during handshake
    azureus = ("-MD0417-").encode("utf-8")
    random_bytes = random.randbytes(12)
    myid = azureus + random_bytes
    print("My id is " + str(myid) + "\n")
    
    # make and/or clear file to hold our single torrent-file answer
    torrent_file_path = "tor-file-examples/cosmos-laundromat.torrent"
    torrent_name_list = torrent_file_path.split("/")
    output_file_name = (torrent_name_list[len(torrent_name_list) - 1].split("."))[0] + "_bytes"
    output_file = open(output_file_name, "wb")
    
    
    # used to poll over peer sockets 
    sel = selectors.DefaultSelector() 
    
    # get visible IP of this machine - requires requests library (or manual conversation with an external host);
    # see https://stackoverflow.com/questions/17309288/importerror-no-module-named-requests;
    # probably not actually necessary for this assigment - the tracker determines and advertises
    # your ip via the socket connection you have with it;
    # this also might not work in docker or VM
    ip = requests.get('https://checkip.amazonaws.com').text.strip() 
    print("my ip is: " + str(ip))
    
    # port on which to listen and accept peer connections, communicated to tracker 
    # in practice we are going to have to be the one initating connections to our peers because
    # no one is going to be able to get through our internet firewall 
    port = 1025 # port = int(sys.argv[1]) # should this be user-set?
    
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.bind(("0.0.0.0", port)) 
    listen_sock.listen(5) # listen to a max of 5 queued connections, standard for bittorrent
    
    sel.register(listen_sock, selectors.EVENT_READ)
    
    # Get information from torrent file about piece length and total number of pieces
    torrent_file = open(torrent_file_path, 'rb')
    info_dict = bdecode(torrent_file)["info"]
    
    output_file_length = 0
    piece_length = info_dict["piece length"]
    hashes = info_dict["pieces"]
    
    if "files" in info_dict: 
        # mult-file 
        for file_dict in info_dict["files"]:
            output_file_length += file_dict["length"]
    else: 
        # single file
        output_file_length = info_dict["length"]
        
    num_pieces = math.ceil(output_file_length / piece_length)
    
    block_length = 16000 # MAX = 16000
    if (piece_length < block_length):
        print("Default block size of 16KiB being down-adjusted to match piece length\n")
        block_length = piece_length
        
    blocks_per_piece = math.ceil(piece_length / block_length)
    
    print("This file has " + str(num_pieces) + " pieces, with " + str(blocks_per_piece) + " blocks per piece\n")
    
    # Get information from tracker about peers
    metadata = get_info_from_tracker_specified_in_file(torrent_file_path, port, event='started')
        
    # peers (in metadata) can either be a dictionary or a bytestring in the following format:
    # 4 bytes for ip address of peer 1, 2 bytes for port of peer 1, 4 bytes for ip of peer 2, 2 bytes for port
    # of peer 2, etc.
    # metadata = {"interval": 100, "peers":[{"peer id": 5, "ip": "127.0.0.1", "port": 1024}]}
    
    if ("failure reason" in metadata): 
        print("Failed to get metadata from tracker: " + metadata["failure reason"] + "\n")
        exit()
    
    interval = metadata["interval"]
    peers = metadata["peers"]
    # print("Metadata is: " + str(metadata) + "\n")
    swarm: list[Bee] = list()
    num_bees = 0
    compact = False
    
    if (not isinstance(peers, list)):
        # tracker is in compact mode
        # peers are one large byte string, with no peer id furnished
        compact = True
        peers = [peers[i:i+6] for i in range(0, len(peers), 6)]
    
    
    # For each peer, create a Bee to store their state and do a 
    # handshake with them
    for peer in peers:
        newbie = Bee(num_pieces)
        
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
            newbie.sock.close()
        else: 
            # recommended to set non blocking for use with selectors, so in case of edge cases the program won't hang
            # kept the socket blocking durring connect() so that we know if connect failures are from 
            # server not responding (timeout) or server actively rejecting us
            print("Sucesfully connected to peer " + str(newbie.addr) + "\n")
            newbie.sock.setblocking(False) 
            swarm.append(newbie)
            num_bees += 1
    
    # Tell all peers that they are choked and we are not interested 
    for bee in swarm: 
        send_message_tcp(choke_msg, bee.sock)
        send_message_tcp(not_interested_msg, bee.sock)
        print(bee.to_string())
    
    auction_clock = time.monotonic() # 10 seconds should elapse before every non-optimistic choke/unchoke
    charity_clock = time.monotonic() # 30 seconds should elapse before every optimistic unchokex
    tracker_clock = time.monotonic() # interval seconds should elapse before we update tracker with our status and how much we've downloaded/uploaded
    
    # Begin main logic to handle never-ending byte stream of <prefix_len><msg>
    piecelist = PieceList(num_pieces, piece_length, blocks_per_piece, block_length, output_file, hashes)
    output_file.write(b'\x00' * output_file_length)
    
    def handle_msg(prefix_len, bee):
        if (prefix_len == 0):
            handle_keepalive(bee)
        else: 
            msg = recv_message_tcp(bee.sock, prefix_len)
            match (msg[5]):
                case 0: 
                    handle_choke(bee, msg)
                case 1:
                    handle_unchoke(bee, msg)
                case 2: 
                    handle_interested(bee, msg)
                case 3:
                    handle_not_interested(bee, msg)
                case 4:
                    handle_have(bee, msg)
                case 5:
                    handle_bitfield()
                case 6:
                    handle_request(bee, msg, piecelist)
                case 7:
                    # calculate block length (X) from prefix_len - 9 (see wikitheory specs)
                    X = prefix_len - 9
                    if (handle_piece(bee, msg, X, piecelist)):
                        # keep track of who uploaded us the most number of blocks (all block sizes are the same,
                        # except for irregular blocks at the end of pieces, so estimate by counting by number of blocks)
                        bee.blocks_uploaded += 1
                case 8:
                    handle_cancel(bee, msg)
                case 9:
                    handle_port()
                case _: 
                    print("Peer message received with unkown ID " + msg[5])
    
    
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
                    msg = recv_message_tcp(curr.sock, 4)
                    prefix_len = int.from_bytes(msg[0:5:1], byteorder="big")
                    handle_msg(prefix_len, curr)
                
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


if __name__=="__main__":
    main()