import socket
import selectors
from bcoding import bencode, bdecode

def main():
    torfile = open("tor-file-examples/cosmos-laundromat.torrent", 'rb')
    tde = bdecode(torfile)
    print(tde)
    
    

if __name__=="__main__":
    main()