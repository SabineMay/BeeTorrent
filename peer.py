import socket
import selectors
import sys
from bcoding import bencode, bdecode
import hashlib

# Test file for sending between peers
# arguments -p port_num -s {optional, indicates server mode}

def main():
    torfile = open("tor-file-examples/cosmos-laundromat.torrent", 'rb')
    tde = bdecode(torfile)
    info_hash = hashlib.sha1(tde['info']['pieces'])
    info_hash = info_hash.digest()




    ipa = socket.gethostbyname(socket.gethostname())
    port = int(sys.argv[2])
    '''

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Server mode
    if (len(sys.argv) > 3):
       sock.bind((ipa, port))

       sock.listen(100)

       (clisock, addr) = sock.accept()

       #length = (5).to_bytes(4, 'big')
       pstr = "BitTorrent protocol"
       pstrlen = len(pstr)
       res = bytearray(8)



       #clisock.send(length)

       clisock.close()
       sock.close()
    
    # Client mode
    else:
        sock.connect((ipa, port))

        #mes = sock.recv(4)

        #length = int.from_bytes(mes, "big")

        if length > 0:
            id = sock.recv(1)

            id = int.from_bytes(id)

            print(id)
        


        #print(length)
        sock.close()
    '''
    
    

if __name__=="__main__":
    main()