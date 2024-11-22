import socket
import selectors
import bencodepy
from bcoding import bencode, bdecode

def main():
    torfile = open("lots-of-numbers.torrent", 'rb')
    tde = bdecode(torfile)
    
    

if __name__=="__main__":
    main()