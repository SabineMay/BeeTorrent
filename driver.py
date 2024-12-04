import selectors
import socket 
import sys
from Bee import Bee
from get_info_from_tracker import *
import time
import random
from handshake import *
from errors import *
from construct_messages import *
from handle_messages import *
import math
from PieceList import PieceList
from operator import itemgetter
from bcoding import bencode, bdecode
from download_strat import *

TORRENT_FILE_PATH = 'tor-file-examples/cosmos-laundromat.torrent'
MAX_PENDING_REQUESTS = 1

def main():
    """
    Add some comments here detailing what variables we are keeping to maintain our own state and
    the state of our peers.
    
    Ex. 
    swarm: list of Bees | all state information on peers (socket, bitfield, etc)
    piecelist: PieceList | state information about our pieces and blocks
    myid: bytes | id that we advertise to tracker during GET and advertise to peers during handshake
    output_file: byte file | file into which we write incoming blocks
    
    listen_sock | sock on which we listen for incoming peer connections; 
                | will probably never get any action because we are behind a firewall 
    """
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

    
    # make and/or clear file to hold our single torrent-file answer
    torrent_file_path = TORRENT_FILE_PATH
    torrent_name_list = torrent_file_path.split("/")
    output_file_name = (torrent_name_list[len(torrent_name_list) - 1].split("."))[0] + "_bytes"
    output_file = open(output_file_name, "w+b")
    
    
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
    
    # port on which to listen and accept peer connections, communicated to tracker 
    # in practice we are going to have to be the one initating connections to our peers because
    # no one is going to be able to get through our internet firewall 
    port = 6881 # port = int(sys.argv[1]) # should this be user-set?
    
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
    
    
    # Get information from torrent file about piece length and total number of pieces
    torrent_file = open(torrent_file_path, 'rb')
    info_dict = bdecode(torrent_file)["info"]
    
    output_file_length = 0
    piece_length = info_dict["piece length"]
    hashes = []

    # hashes are returned as 1 giant bytestring instead of a list of bytestrings
    # so transform it into a list of bytestrings
    current = b''
    i = 0
    for byte in info_dict["pieces"]:
        current += byte.to_bytes(1)
        i += 1
        if i >= 20:
            hashes.append(current)
            current = b''
            i = 0


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
            log_error(Exception("Could not connect to peer " + str(newbie.addr) + " (" + (str(e)) + ")"))
            newbie.sock.close()
        else: 
            # recommended to set non blocking for use with selectors, so in case of edge cases the program won't hang
            # kept the socket blocking durring connect() so that we know if connect failures are from 
            # server not responding (timeout) or server actively rejecting us
            try:
                send_handshake(newbie.sock, info_hash, myid)
                recv_handshake(newbie.sock)
                #print(info_hash)
                print("Sucesfully connected to peer " + str(newbie.addr) + "\n")
                newbie.sock.setblocking(False) 
                swarm.append(newbie)
                num_bees += 1
            except Exception as e:
                print("Failed to handshake with peer " + str(newbie.addr) + "\n")
                log_error(Exception("Failed handshake with " + str(newbie.addr) +  ": " + str(e)))
    
    if not swarm: 
        print("No Bees in swarm!\n")
        exit()
    
    # Tell all peers that they are choked and we are not interested 
    for bee in swarm: 
        send_message_tcp(choke_msg, bee.sock)
        send_message_tcp(not_interested_msg, bee.sock)
        sel.register(bee.sock, selectors.EVENT_READ)
        print(bee.to_string())
    
    auction_clock = time.monotonic() # 10 seconds should elapse before every non-optimistic choke/unchoke
    charity_clock = time.monotonic() # 30 seconds should elapse before every optimistic unchokex
    keep_alive_clock = time.monotonic() # Clock to keep track of when we should send keepalives
    tracker_clock = time.monotonic() # interval seconds should elapse before we update tracker with our status and how much we've downloaded/uploaded
    
    # Begin main logic to handle never-ending byte stream of <prefix_len><msg>
    piecelist = PieceList(num_pieces, piece_length, blocks_per_piece, block_length, output_file, hashes)
    output_file.write(b'\x00' * output_file_length)

    
    
    def handle_msg(prefix_len, bee):
        try:
            if (prefix_len == 0):
                handle_keepalive(bee)
            else: 
                msg = recv_message_tcp(bee.sock, prefix_len)
                match (msg[0]):
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
                        handle_bitfield(bee, msg)
                    case 6:
                        handle_request(bee, msg, piecelist)
                    case 7:
                        # calculate block length (X) from prefix_len - 9 (see wikitheory specs)
                        X = prefix_len - 9
                        if (handle_piece(bee, msg, X, piecelist)):
                            # keep track of who uploaded us the most number of blocks (all block sizes are the same,
                            # except for irregular blocks at the end of pieces, so estimate by counting by number of blocks)
                            bee.blocks_uploaded += 1
                        bee.num_pending_requests_sent -= 1
                    case 8:
                        handle_cancel(bee, msg)
                    case 9:
                        handle_port()
                    case _: 
                        print("Peer message received with unkown ID " + str(msg[5]))
        except SocketDisconnected as e:
            log_error(Exception("Error in handle_msg with " + bee.to_string() + ": " + str(e)))
    
    rarest_list = []
    while(True):
        events = sel.select(timeout = 1) # potential issue: need to adjust timeout based on how much time left on auction/tracker/charity clocks
        
        for key, mask in events: 
            
            # getting a connect() message from a peer
            if (key.fd == listen_sock): 
                addr, sock = key.fd.accept()

                print("connect message received")
            
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
                    try:
                        recv_handshake(sock)
                        send_handshake(sock, info_hash, myid)
                        # delete peer and close socket if handshake failed
                        sel.register(sock, selectors.EVENT_READ)
                        newbie = Bee(num_pieces)
                        newbie.sock = sock
                        swarm.append(newbie)
                        num_bees += 1
                    except SocketDisconnected as e:
                        log_error(Exception("Exception when handshaking with a bee that was not in the tracker: " + str(e)))
                    
            
            # getting a message from a peer on an already-established socket
            else: 
                curr = None

                for bee in swarm: 
                    if (key.fd == bee.sock.fileno()): # potential problem: is this the right way to check equality of tuples?
                        bee.reset_clock()
                        curr = bee
                        break
                
                if (curr == None):
                    print("Couldn't find peer assocated with selected socket in swarm")
                else: 
                    try:
                        msg = recv_message_tcp(curr.sock, 4)
                        prefix_len = int.from_bytes(msg, byteorder="big")
                        handle_msg(prefix_len, curr)
                    except SocketDisconnected as e:
                        # if we run into an error when receiving a message from the bee
                        # then remove the bee from the swarm
                        log_error(Exception("Exception when receiving message from " + curr.to_string() + ": " + str(e)))
                        print("Error receiving a message from " + curr.to_string() + ", removing from the swarm")
                        sel.unregister(curr.sock)
                        swarm.remove(curr)
                        num_bees -= 1
                    
                
        for bee in swarm: 
            if (bee.get_time_elapsed() > 120): # 2 minutes since last message
                sel.unregister(bee.sock)
                swarm.remove(bee)
                num_bees -= 1
        
        # first, check the bees that have pieces we're interested in
        for bee in swarm:
            if (rarest_list == []):
                rarest_list = get_rarest_list(swarm)
                #print(rarest_list)
            try:
                if piecelist.check_interest(bee.bitfield):
                    if not bee.me_interested:
                        send_message_tcp(interested_msg, bee.sock)
                        bee.me_interested = True
                else:
                    if bee.me_interested:
                        send_message_tcp(not_interested_msg, bee.sock)
                        bee.me_interested = False
            except SocketDisconnected as e:
                log_error(Exception("Exception when sending interested message to " + bee.to_string() + ": " + str(e)))
                print("Error sending interested message to " + bee.to_string())
            
        
        # next, request pieces that we're interested in
        # TODO: get a better strategy than just requesting the next needed block.
        # once we do that, we should adjust MAX_PENDING_REQUESTS to smth else
        for bee in swarm:
            if bee.me_interested and not bee.me_choked and bee.num_pending_requests_sent < MAX_PENDING_REQUESTS:
                piece_idx = get_rarest_piece_needed(bee, piecelist, rarest_list)
                block_idx = piecelist.get_needed_block_for_piece(piece_idx)

                if piece_idx != -1 and block_idx != -1:
                    block_length = piecelist.block_length
                    if block_idx == piecelist.blocks_per_piece - 1:
                        block_length = piecelist.piece_length - (block_length * (piecelist.blocks_per_piece - 1))
                    #print(piece_idx, block_idx)
                    send_message_tcp(construct_request_msg(piece_idx, block_idx * piecelist.block_length, block_length), bee.sock)
                    piecelist.request(piece_idx, block_idx)
                    bee.num_pending_requests_sent += 1

                # returns next block that hasn't been RECEIVED, we should pick
                # a better strategy
                '''
                (piece_idx, block_idx) = piecelist.next_needed_block()

                if piece_idx == -1 and block_idx == -1:
                    # TODO pick what to do once we get the whole file
                    print('yippee')
                    pass
                else:
                    block_length = piecelist.block_length
                    if block_idx == piecelist.blocks_per_piece - 1:
                        block_length = piecelist.piece_length - (block_length * (piecelist.blocks_per_piece - 1))
                    send_message_tcp(construct_request_msg(piece_idx, block_idx * piecelist.block_length, block_length), bee.sock)
                    piecelist.request(piece_idx, block_idx)
                    bee.num_pending_requests_sent += 1
                '''

        curr_time = time.monotonic()

        if curr_time - keep_alive_clock >= 30:
            
            for bee in swarm:
                send_message_tcp(keep_alive_msg, bee.sock)
            keep_alive_clock = time.monotonic()

        if (curr_time - auction_clock >= 10):
            # recalculate top 4 interested uploaders 
            scoreboard = []
            for bee in swarm:
                scoreboard.append((bee, bee.blocks_uploaded))
            
            scoreboard.sort(key=itemgetter(1), reverse=True)

            i = 0
            while i < 4 and i < len(scoreboard):
                send_message_tcp(unchoke_msg, (scoreboard[i])[0].sock)
                (scoreboard[i])[0].peer_choked = 0
                #print(scoreboard[i][1])
                i += 1

            auction_clock = time.monotonic() # reset clock

        if (curr_time - charity_clock >= 30):
            # optimistically unchoke a new person 
            unchoke_peer = random.choice(swarm)
            # Check if peer is already unchoked
            send_message_tcp(unchoke_msg, unchoke_peer.sock)
            unchoke_peer.peer_choked = 0
            charity_clock = time.monotonic() # reset clock


if __name__=="__main__":
    main()
