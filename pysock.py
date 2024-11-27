import socket
import selectors
import construct_http_requests
from bcoding import bencode, bdecode

def main():
    '''
    torfile = open("tor-file-examples/cosmos-laundromat.torrent", 'rb')
    tde = bdecode(torfile)
    addrstr = tde['announce']
    addrsep = addrstr.split(':')
    ip_addr = addrsep[0] + addrsep[1]
    port = addrsep[2]
    print(port) # ensure main() is actually running when you execute ~/cmsc417-BitTorrent/venv/bin/python3 {FILENAME}.py
    '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("www.example.com", 80))

    msg = construct_http_requests.construct_GET_request("example.com", 80, "/")
    
    totalsent = 0
    while totalsent < len(msg):
        sent = sock.send(msg[totalsent:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent

if __name__=="__main__":
    main()
