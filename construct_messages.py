import socket

keep_alive_msg = bytes([0, 0, 0, 0])
choke_msg = bytes([0, 0, 0, 1, 0])
unchoke_msg = bytes([0, 0, 0, 1, 1])
interested_msg = bytes([0, 0, 0, 1, 2])
not_interested_msg = bytes([0, 0, 0, 1, 3])

def construct_have_msg(piece_idx):
    # piece_idx = socket.htonl(piece_idx)
    piece_bytes = int.to_bytes(piece_idx, 4, byteorder="big")
    ret = bytearray([0, 0, 0, 5, 4])
    
    for b in piece_bytes:
        ret.append(b)
        
    return ret

def construct_request_msg(idx, begin, length): 
    # idx = socket.htonl(idx)
    # begin = socket.htonl(begin)
    # length = socket.htonl(length)
    
    idx_bytes = int.to_bytes(idx, 4, byteorder="big")
    begin_bytes = int.to_bytes(begin, 4, byteorder="big")
    length_bytes = int.to_bytes(length, 4, byteorder="big")
    
    ret = bytearray([0, 0, 0, 13, 6])
    
    for b in idx_bytes:
        ret.append(b)
    for b in begin_bytes:
        ret.append(b)
    for b in length_bytes:
        ret.append(b)
    
    return ret

def construct_piece_msg(idx, begin, block_bytes): 
    x = len(block_bytes)
    # idx = socket.htonl(idx)
    # begin = socket.htonl(idx)
    
    idx_bytes = int.to_bytes(idx, 4, byteorder="big")
    begin_bytes = int.to_bytes(begin, 4, byteorder="big")
    
    ret = bytearray([(9 + x), 7])
    for b in idx_bytes:
        bytearray.append(b)
    for b in begin_bytes:
        bytearray.append(b)
    for b in block_bytes: 
        bytearray.append(b)
        
    return ret
        

def construct_cancel_msg(): 
    # idx = socket.htonl(idx)
    # begin = socket.htonl(idx)
    # length = socket.htonl(idx)
    
    idx_bytes = int.to_bytes(idx, 4, byteorder="big")
    begin_bytes = int.to_bytes(begin, 4, byteorder="big")
    length_bytes = int.to_bytes(length, 4, byteorder="big")
    
    ret = bytearray([0, 0, 0, 13, 8])
    
    for b in idx_bytes:
        ret.append(b)
    for b in begin_bytes:
        ret.append(b)
    for b in length_bytes:
        ret.append(b)
    
    return ret