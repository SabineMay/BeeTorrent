from errors import *
import socket
import ssl


# sends a message over a connected socket
def send_message_tcp(msg, sock):
    total_sent = 0
    while total_sent < len(msg):
        try:
            sent = sock.send(msg[total_sent:])
        except BlockingIOError as e:
            # if the socket is temporarily unavailable, wait until its fine
            continue
        except:
            raise SocketDisconnected("socket disconnected during send")
        if sent == 0:
            raise SocketDisconnected("socket disconnected during send")
        total_sent = total_sent + sent

# receives a message over a given socket
def recv_message_tcp(sock, size):
    total_recv = 0
    msg = b''
    while total_recv < size:
        try:
            received = sock.recv(size - total_recv)
        except BlockingIOError as e:
            # if the socket is temporarily unavailable, wait until its fine
            continue
        except:
            raise SocketDisconnected("socket disconnected during send")
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
        raise UnexpectedPacket(f"received non-200 response in recv_http_response: {next_string}")
    
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

    print(http_response)
    print(f"AND THE BODY IS {http_body}")

    if ("Transfer-Encoding: chunked" in http_response):
        # Chunked response, more complicated recv procedure
        http_body = recv_chunked_response(sock)

    return http_body

def recv_chunked_response(sock: ssl.SSLSocket):
    response_body = b""

    while True:
        # Read chunk size
        chunk_size_hex = read_until(sock, b"\r\n")
        print(f"The chunk size for this one is {repr(chunk_size_hex)}")

        try:
            chunk_size = int(chunk_size_hex, 16)
            print(f"CHUNK SIZE: {chunk_size}")
        except ValueError:
            raise ValueError(f"Invalid chunk size: {chunk_size_hex}")
        
        # signifies end of chunks of data
        if chunk_size == 0:
            break

        chunk_data = b""
        while len(chunk_data) < chunk_size:
            partial_chunk = sock.recv(chunk_size - len(chunk_data))
            chunk_data += partial_chunk
        
        print(f"The chunk data for this one is {repr(chunk_data)}")

        response_body += chunk_data

        # skip over CRLF
        sock.recv(2)
    
    return response_body

def read_until(sock, delim: str):
    data = b""
    while True:
        byte = sock.recv(1)
#        print(f"BYTE: {repr(byte)}")

        data += byte
        if data.endswith(delim):
            print("Delimiter found! Breaking...")
            break
    return data[:-(len(delim))]

