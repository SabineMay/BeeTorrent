from send_receive_message import *

def send_handshake(socket, info_hash, peer_id):
    
    pstr = "BitTorrent protocol"
    pstrlen = (len(pstr)).to_bytes(1)
    reserved = bytearray(8) # Figure out what reserved bits are

    send_message_tcp(pstrlen, socket)
    send_message_tcp(pstr.encode("utf-8"), socket)
    send_message_tcp(reserved, socket)
    send_message_tcp(info_hash, socket)
    send_message_tcp(peer_id, socket)


def recv_handshake(socket):
    msg = recv_message_tcp(socket, 68)
    #print(msg)


