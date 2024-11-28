import socket
import selectors
from torrent_get_requests import *
from send_receive_message import *
from bcoding import bencode, bdecode

def main():
    # connect to the tracker
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("bt1.archive.org", 6969))

    # send a get request to the tracker for this torrent
    msg = create_torrent_get_request_from_file("tor-file-examples/kali-linux.torrent", 6881, event='started')
    send_message(msg, sock)

    # receive the response back, the payload of the http response is stored in resp
    resp = recv_http_response(sock)

    # decode and print 
    print(bdecode(resp))

if __name__=="__main__":
    main()
