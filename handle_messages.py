from Bee import Bee
from PieceList import PieceList
from construct_messages import *
from send_receive_message import *
from Request import Request

def handle_keepalive(bee: Bee, msg): 
    bee.reset_clock()

def handle_choke(bee: Bee, msg):
    bee.me_choked = True

def handle_unchoke(bee: Bee, msg):
    bee.me_choked = False

def handle_interested(bee: Bee, msg):
    bee.peer_interested = True

def handle_not_interested(bee: Bee, msg):
    bee.peer_interested = False

def handle_have(bee: Bee, msg):
    piece_idx = int.from_bytes(msg[1:5:1])
    bee.bitfield.set(True, piece_idx)

def handle_bitfield():
    print("No support for bitfield requests") # TODO: probably can implement this fairly easily, need decide if we need to send back a "can't do this" message if not

def handle_request(bee: Bee, msg, piecelist: PieceList, output_file):
    idx = int.from_bytes(msg[1:5:1], byteorder="big")
    begin = int.from_bytes(msg[5:9:1], byteorder="big")
    length = int.from_byte(msg[9:13:1], byteorder="big")
    if (bee.peer_choked):
        print("Request refused -- peer is choked\n")
        print("Adding request to peer's queue\n")
        bee.queue_request(Request(idx, begin, length))
    elif (piecelist.is_resolved(idx)): 
        print("Request answered -- peer is unchoked and we have the piece\n")
        output_file.seek((idx * PieceList.piece_length) + begin, 0)
        send_message_tcp(construct_request_msg(idx, begin, output_file.read(length)), bee.sock)
    else:
        print("Request refused -- peer is unchoked byt we don't have the piece\n")
        # question: peers should only request pieces we have, but if they don't...
        # do we need to tell peer why this request was refused?

def handle_piece(bee: Bee, msg, block_len, piecelist: PieceList, output_file):
    idx = int.from_bytes(msg[1:5:1], byteorder="big")
    begin = int.from_bytes(msg[5:9:1], byteorder="big")
    
    if (piecelist.is_resolved(idx)):
        print("Got a piece that we already knew\n")
    elif (piecelist.is_requested(idx)):
        block = msg[9:block_len:1]
        output_file.seek((idx * PieceList.piece_length) + begin, 0)
        output_file.write(block)
        
        # TODO: need to verify hash of piece when full piece is accumulated, and only mark as resolved once that happens
        # Also need to somehow keep track of how specific blocks are remembered
        piecelist.resolve() 
        
        # maybe send out cancels?
        # interesting question bc this piece message might only be giving us a block and not a whole piece 
        # -- should we keep other requests that we already sent because they  might give us different parts of the
        # piece? 
        
        # we shouldn't get overlapping blocks because we control the idx, begin parameters in request
        # all the uploader has to do is respond with the number of bytes we requested
        pass
    elif (piecelist.is_ready()):
        print("Got a piece that we didn't advertise for, or that has an incorrent status in piecelist\n")

def handle_cancel(bee: Bee, msg):
    idx = int.from_bytes(msg[1:5:1], byteorder="big")
    begin = int.from_bytes(msg[5:9:1], byteorder="big")
    length = int.from_byte(msg[9:13:1], byteorder="big")
    bee.bitfield.set(False, idx) # need to maintain something more than a bitfield so that we have an independent request queue for each peer

def handle_port():
    print("No support for port requests -- BT-DHT not implemented") #TODO: decide if we ne to send back a "can't do this message"
