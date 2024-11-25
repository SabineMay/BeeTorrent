import socket
import selectors
from bcoding import bencode, bdecode

def main():
    torfile = open("tor-file-examples/cosmos-laundromat.torrent", 'rb')
    tde = bdecode(torfile)
    addrstr = tde['announce']
    addrsep = addrstr.split(':')
    ip_addr = addrsep[0] + addrsep[1]
    port = addrsep[2]
    # print("test") # ensure main() is actually running when you execute ~/cmsc417-BitTorrent/venv/bin/python3 {FILENAME}.py
    

if __name__=="__main__":
    main()