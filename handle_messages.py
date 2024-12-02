from Bee import Bee
from PieceList import PieceList
from construct_messages import *
from send_receive_message import *
from Request import Request
import math

"""
Module that handles the receipt of peer messages. May send responses to peers
if prompted (like when receiving a request), but does not contain logic for 
self-initiated messages (like when genereating a request).
"""

def handle_keepalive(bee: Bee): 
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
    bee.set_bitfield_at_index(piece_index, True)

def handle_bitfield(bee: Bee, msg):
    bee.update_bitfield_from_received_bitfield(msg[1:])

def handle_request(bee: Bee, msg, piecelist: PieceList):
    idx = int.from_bytes(msg[1:5:1], byteorder="big")
    begin = int.from_bytes(msg[5:9:1], byteorder="big")
    length = int.from_byte(msg[9:13:1], byteorder="big")
    if (bee.peer_choked):
        print("Request refused -- peer is choked\n")
        print("Adding request to peer's queue\n")
        bee.queue_request(Request(idx, begin, length))
    elif (piecelist.is_resolved(idx)): 
        print("Request answered -- peer is unchoked and we have the piece\n")
        piecelist.output_file.seek((idx * PieceList.piece_length) + begin, 0)
        send_message_tcp(construct_have_msg(idx, begin, piecelist.output_file.read(length)), bee.sock)
    else:
        print("Request refused -- peer is unchoked but we don't have the piece\n")
        # question: peers should only request pieces we have, but if they don't...
        # do we need to tell peer why this request was refused?

def handle_piece(bee: Bee, msg, X, piecelist: PieceList):
    if (X != piecelist.block_length):
        print("Peer gave us an incorrectly-sized block\n")
        
    else: 
        print("handling piece")

        piece_idx = int.from_bytes(msg[1:5:1], byteorder="big")
        begin = int.from_bytes(msg[5:9:1], byteorder="big")
        
        # potential problem: need to check my math here
        block_idx = min((begin // piecelist.block_length), piecelist.blocks_per_piece - 1)
        # block_idx = begin // piecelist.block_length

        if (piecelist.is_resolved(piece_idx)):
            print("Got a block for a piece that we already hash-verified\n")
        elif(piecelist.is_received(piece_idx, block_idx)):
            print("Got a block that we already received: \n")
        elif (piecelist.is_requested(piece_idx, block_idx)):
            block = msg[9:]
            piecelist.output_file.seek((piece_idx * piecelist.piece_length) + begin, 0)
            piecelist.output_file.write(block)
            
            # TODO: verify that we are sent back a block we actually asked for before we recieve it
            piecelist.receive(piece_idx, block_idx) 

            # TODO: maybe send out cancels?
            # interesting question bc this piece message might only be giving us a block and not a whole piece 
            # -- should we keep other requests that we already sent because they  might give us different parts of the
            # piece? 
        elif (piecelist.is_ready(piece_idx, block_idx)):
            print("Got a piece that we didn't advertise for, or that has an incorrent status in piecelist\n")

def handle_cancel(bee: Bee, msg):
    idx = int.from_bytes(msg[1:5:1], byteorder="big")
    begin = int.from_bytes(msg[5:9:1], byteorder="big")
    length = int.from_byte(msg[9:13:1], byteorder="big")
    bee.cancel_request(idx, begin, length)

def handle_port():
    print("No support for port requests -- BT-DHT not implemented") #TODO: decide if we ne to send back a "can't do this message"
