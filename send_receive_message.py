from errors import *
import socket


# sends a message over a connected socket
def send_message_tcp(msg, sock):
    total_sent = 0
    while total_sent < len(msg):
        sent = sock.send(msg[total_sent:])
        if sent == 0:
            raise SocketDisconnected("socket disconnected during send")
        total_sent = total_sent + sent

# receives a message over a given socket
def recv_message_tcp(sock, size):
    total_recv = 0
    msg = b''
    while total_recv < size:
        received = sock.recv(size - total_recv)
        if received == b'':
            raise SocketDisconnected("socket disconnected during recv")
        msg += received
        total_recv += len(received)
    return msg


# receives an http response over a given socket.
# returns the body of the response as a raw bytestring
def recv_http_response(sock):
    http_response = ""
    
    # get the first line of the http response in 2 parts

    # first is the 'HTTP/1.1 ' bit to make sure we are receiving an http packet
    next_string = recv_message_tcp(sock, 9).decode()
    
    if (next_string != "HTTP/1.1 "):
        raise UnexpectedPacket("expected http response in recv_http_response, non-http received")
    
    http_response += next_string

    # next is the response code to make sure there was no error
    next_string = recv_message_tcp(sock, 8).decode()

    if (next_string != "200 OK\r\n"):
        raise UnexpectedPacket("received non-200 response in recv_http_response")
    
    http_response += next_string

    continue_recv_http_header = True

    content_length = 0

    # receive the rest of the http header and note the content-length
    while continue_recv_http_header:
        # receive the first 2 bytes of the next line
        current_line = recv_message_tcp(sock, 2).decode()

        # if the next line is just \r\n then we've finished the header
        if current_line == "\r\n":
            http_response += current_line
            continue_recv_http_header = False
            break
        
        # receive the current line until the line ends
        while current_line[(len(current_line) - 2):] != "\r\n":
            current_line += recv_message_tcp(sock, 1).decode()
        
        # detect the length of the body
        if "Content-Length" in current_line:
            content_length = int(current_line.split(": ")[1].split("\r")[0])

        http_response += current_line
    
    # receive the body of the response
    http_body = recv_message_tcp(sock, content_length)

    return http_body