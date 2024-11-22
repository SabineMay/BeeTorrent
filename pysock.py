import socket
import selectors
from bcoding import bencode, bdecode

def main():
    torfile = open("lots-of-numbers.torrent", 'rb')
    tde = bdecode(torfile)
    
    

if __name__=="__main__":
    main()