import socket
import selectors
import sys
from bcoding import bencode, bdecode

# Test file for sending between peers
# arguments -p port_num -s {optional, indicates server mode}

def main():
    ipa = "172.16.45.87"
    port = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Server mode
    if (len(sys.argv) > 3):
       sock.bind((ipa, port))

       sock.listen(5)

       (clisock, addr) = sock.accept()

       msg = bytearray(4)
       msg[0] = 0
       msg[1] = 0
       msg[2] = 0
       msg[3] = 1
       clisock.send(msg)

       id = bytearray(1)
       id[0] = 1

       clisock.send(id)
    
    # Client mode
    else:
        sock.connect((ipa, port))

        mes = sock.recv(4)

        length = int.from_bytes(mes, "big")

        if length > 0:
            id = sock.recv(1)

            id = int.from_bytes(id)

            print(id)


        print(length)
        

    
    

if __name__=="__main__":
    main()