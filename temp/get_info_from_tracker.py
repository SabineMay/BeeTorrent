from construct_http_requests import *
from bcoding import bencode, bdecode
import hashlib
import urllib.parse
import socket
import ssl
from send_receive_message import *
from random import randint
from arg_parser import vlog
import time

NETWORK_ORDER = 'big'
MAGIC_NUMBER_UDP = 0x41727101980
MAX_UDP_PACKET_SIZE = 65507

def create_torrent_get_request_from_file(torrent_file_path, listening_port, my_id, uploaded = 0, downloaded = 0, left = None, event = None):
    torfile = open(torrent_file_path, 'rb')
    tde = bdecode(torfile)

    host_domain = (tde['announce'].replace("http://", "")).split(":")[0]
    port_number = 0
    base_path = ""

    # sometimes the announce address doesn't specify a path, so we assume it's /announce
    if ("/" in (tde['announce'].replace("http://", "")).split(":")[1]):
        port_number = int((tde['announce'].replace("http://", "")).split(":")[1].split("/")[0])
        base_path = "/" + (tde['announce'].replace("http://", "")).split("/")[1]
    else:
        port_number = int((tde['announce'].replace("http://", "")).split(":")[1])
        base_path = "/announce"

    h = hashlib.sha1()

    h.update(bencode(tde['info']))

    params = {}
    
    params['info_hash'] = urllib.parse.quote_from_bytes(h.digest())

    params['peer_id'] = urllib.parse.quote_from_bytes(my_id)

    params['port'] = str(listening_port)

    params['uploaded'] = str(uploaded)

    params['downloaded'] = str(downloaded)


    if left != None:
        params['left'] = str(left)
    else:
        if 'length' in tde['info'].keys():
            params['left'] = str(int(tde['info']['length']) - downloaded)
        else:
            if 'files' in tde['info'].keys():
                l = 0
                for f in tde['info']['files']:
                    l += int(f['length'])
                params['left'] = str(l - downloaded)

    if event != None:
        params['event'] = event

    complete_path = create_path(base_path, params)

    return construct_GET_request(host_domain, port_number, complete_path)

# used for HTTPS tracker
def create_torrent_get_request_from_info(host_domain, port_number, base_path, tde, listening_port, my_id, uploaded = 0, downloaded = 0, left = None, event = None):

    h = hashlib.sha1()

    h.update(bencode(tde['info']))

    params = {}
    
    params['info_hash'] = urllib.parse.quote_from_bytes(h.digest())

    params['peer_id'] = urllib.parse.quote_from_bytes(my_id)

    params['port'] = str(listening_port)

    params['uploaded'] = str(uploaded)

    params['downloaded'] = str(downloaded)


    if left != None:
        params['left'] = str(left)
    else:
        if 'length' in tde['info'].keys():
            params['left'] = str(int(tde['info']['length']) - downloaded)
        else:
            if 'files' in tde['info'].keys():
                l = 0
                for f in tde['info']['files']:
                    l += int(f['length'])
                params['left'] = str(l - downloaded)

    if event != None:
        params['event'] = event

    complete_path = create_path(base_path, params)

    return construct_GET_request(host_domain, port_number, complete_path)

def rand_transaction_id():
    return randint(0, 4294967295)

def udp_tracker_timeout(n):
    return 15 * (2 ** n)

def create_udp_connect_request(transaction_id):
    connect_request = b''

    action = 0

    # Offset  Size            Name            Value
    # 0       64-bit integer  protocol_id     0x41727101980 // magic constant
    # 8       32-bit integer  action          0 // connect
    # 12      32-bit integer  transaction_id
    # 16
    connect_request += MAGIC_NUMBER_UDP.to_bytes(8, NETWORK_ORDER)
    connect_request += action.to_bytes(4, NETWORK_ORDER)
    connect_request += transaction_id.to_bytes(4, NETWORK_ORDER)

    return connect_request

def create_udp_announce_request(connection_id_bytes, transaction_id, tde, listening_port, peer_id, uploaded, downloaded, left, event):
    if left == None:
        if 'length' in tde['info'].keys():
            left = int(tde['info']['length']) - downloaded
        else:
            if 'files' in tde['info'].keys():
                l = 0
                for f in tde['info']['files']:
                    l += int(f['length'])
                left = l - downloaded

    #     Offset  Size    Name    Value
    # 0       64-bit integer  connection_id
    # 8       32-bit integer  action          1 // announce
    # 12      32-bit integer  transaction_id
    # 16      20-byte string  info_hash
    # 36      20-byte string  peer_id
    # 56      64-bit integer  downloaded
    # 64      64-bit integer  left
    # 72      64-bit integer  uploaded
    # 80      32-bit integer  event           0 // 0: none; 1: completed; 2: started; 3: stopped
    # 84      32-bit integer  IP address      0 // default
    # 88      32-bit integer  key
    # 92      32-bit integer  num_want        -1 // default
    # 96      16-bit integer  port
    # 98
    announce_request = b''
    announce_request += connection_id_bytes
    
    action = 1
    announce_request += action.to_bytes(4, NETWORK_ORDER)

    announce_request += transaction_id.to_bytes(4, NETWORK_ORDER)

    # info hash
    h = hashlib.sha1()
    h.update(bencode(tde['info']))
    announce_request += h.digest()

    # peer id
    announce_request += peer_id

    # uploaded, downloaded, and left
    announce_request += downloaded.to_bytes(8, NETWORK_ORDER)
    announce_request += uploaded.to_bytes(8, NETWORK_ORDER)
    announce_request += left.to_bytes(8, NETWORK_ORDER)

    # event
    event_num = {'none': 0, 'completed': 1, 'started': 2, 'stopped': 3}[event]
    announce_request += event_num.to_bytes(4, NETWORK_ORDER)

    # ip address (default 0)
    ip = 0
    announce_request += ip.to_bytes(4, NETWORK_ORDER)

    # random integer for key
    key = rand_transaction_id()
    announce_request += key.to_bytes(4, NETWORK_ORDER)

    num_want = -1
    announce_request += num_want.to_bytes(4, NETWORK_ORDER, signed = True)

    announce_request += listening_port.to_bytes(2, NETWORK_ORDER)

    return announce_request





def perform_udp_tracker_protocol(sock, torrent_file_path, listening_port, peer_id, uploaded = 0, downloaded = 0, left = None, event = 'started'):
    torfile = open(torrent_file_path, 'rb')
    tde = bdecode(torfile)
    
    host_domain = (tde['announce'].replace("udp://", "")).split(":")[0]
    port_number = 0

    # get port number from torrent file
    if ("/" in (tde['announce'].replace("udp://", "")).split(":")[1]):
        port_number = int((tde['announce'].replace("udp://", "")).split(":")[1].split("/")[0])
    else:
        port_number = int((tde['announce'].replace("udp://", "")).split(":")[1])


    while True:
        # n for timeout
        n = 0
        
        # send the initial connect request and record when it was sent
        transaction_id = rand_transaction_id()
        connect_request = create_udp_connect_request(transaction_id)
        last_connect_request_send_time = time.time()
        last_connect_response_recv_time = None
        sock.sendto(connect_request, (host_domain, port_number))

        recvd = None

        while n < 9:
            # set a timeout dependent on n and wait for a response
            sock.settimeout(udp_tracker_timeout(n))
            recvd = None
            try:
                (recvd, addr) = sock.recvfrom(16)

                # compare received transaction id to sent
                recvd_trid_bytes = recvd[4:8]

                if recvd_trid_bytes != transaction_id.to_bytes(4, NETWORK_ORDER):
                    # if we got a response we didn't expect, raise error
                    raise UnexpectedPacket("perform_udp_tracker_protocol, received unexpected transaction id in response to connect request")
                else:
                    last_connect_response_recv_time = time.time()
                    break
            except socket.timeout:
                # if we don't get a response
                # send another request
                last_connect_request_send_time = time.time()
                sock.sendto(connect_request, (host_domain, port_number))

                # increase n
                n += 1

                # go to the next loop iteration
                continue
        
        # if we didn't get an answer, raise an error
        if n >= 9:
            raise socket.timeout("perform_udp_tracker_protocol timed out when waiting for connect response")
        
        recvd_connection_id_bytes = recvd[8:]

        transaction_id = rand_transaction_id()
        
        announce_request = create_udp_announce_request(recvd_connection_id_bytes, transaction_id, tde, listening_port, peer_id, uploaded, downloaded, left, event)

        sock.sendto(announce_request, (host_domain, port_number))

        n = 0

        need_to_send_another_connect_request = False

        while n < 9:
            # set a timeout dependent on n and wait for a response
            sock.settimeout(udp_tracker_timeout(n))
            recvd = None
            try:
                (recvd, addr) = sock.recvfrom(MAX_UDP_PACKET_SIZE)

                # compare received transaction id to sent
                recvd_trid_bytes = recvd[4:8]

                if recvd_trid_bytes != transaction_id.to_bytes(4, NETWORK_ORDER):
                    # if we got a response we didn't expect, retry
                    raise UnexpectedPacket("perform_udp_tracker_protocol, received unexpected transaction id in response to announce request")
                else:
                    break
            except socket.timeout:
                # if we don't get a response
                # send another request
                sock.sendto(announce_request, (host_domain, port_number))

                # increase n
                n += 1

                if (time.time() > last_connect_response_recv_time + 60):
                    need_to_send_another_connect_request = True
                    break

                # go to the next loop iteration
                continue
            
        # if we need to send another connect request and restart the process, do so
        if need_to_send_another_connect_request:
            continue
        
        if n >= 9:
            raise socket.timeout("perform_udp_tracker_protocol timed out when waiting for announce response")

        num_leechers = int.from_bytes(recvd[12:16], NETWORK_ORDER)
        num_seeders = int.from_bytes(recvd[16:20], NETWORK_ORDER) 

        peers = recvd[20:]
        
        return {'peers': peers, 'interval': int.from_bytes(recvd[8:12], NETWORK_ORDER)}
            


    




# function that returns metadata from tracker
def get_info_from_tracker_specified_in_file(torrent_file_path, listening_port, peer_id, uploaded = 0, downloaded = 0, left = None, event = 'started'):
    torfile = open(torrent_file_path, 'rb')
    tde = bdecode(torfile)

    vlog(f"\nConnecting to tracker at {tde['announce']}...")

    if "http://" in tde['announce']:
        # get host domain from torrent file
        vlog("Handling this as an HTTP tracker!\n")
        host_domain = (tde['announce'].replace("http://", "")).split(":")[0]
        port_number = 0

        # get port number from torrent file
        if ("/" in (tde['announce'].replace("http://", "")).split(":")[1]):
            port_number = int((tde['announce'].replace("http://", "")).split(":")[1].split("/")[0])
        else:
            port_number = int((tde['announce'].replace("http://", "")).split(":")[1])

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # TODO set socket timeout?
        sock.connect((host_domain, port_number))

        # send a get request to the tracker for this torrent
        msg = create_torrent_get_request_from_file(torrent_file_path, listening_port, peer_id, uploaded = uploaded, downloaded = downloaded, left = left, event = event)
        
        try:
            send_message_tcp(msg, sock)
            # receive the response back, the payload of the http response is stored in resp
            resp = recv_http_response(sock)
        except socket.timeout:
            raise socket.timeout("Timeout when connecting to http tracker")


        # decode and return
        return bdecode(resp)
    elif "udp://" in tde['announce']:
        vlog("Handling this as a UDP tracker!\n")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        tracker_info = perform_udp_tracker_protocol(sock, torrent_file_path, listening_port, peer_id, uploaded = uploaded, downloaded = downloaded, left = left, event = event)

        # decode and return
        return tracker_info
    elif "https://" in tde['announce']:
        # https tracker
        vlog("Handling this as an HTTPS tracker!\n")
        sliced = tde['announce'].replace("https://", "")
        host_domain = None
        base_path = "/announce"
        port_num = 443

        if (":" in sliced):
            # there is a specified port
            host_domain = sliced.split(":")[0]
            if ("/" in sliced):
                port_num = int(sliced.split(":")[1].split("/")[0])
                base_path = "/" + sliced.split("/")[1]
            else:
                port_num = int(sliced.split(":")[1])
        else:
            # there is not a specified port
            if ("/" in sliced):
                host_domain = sliced.split("/")[0]
                base_path = "/" + sliced.split("/")[1]
            else:
                host_domain = sliced

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # TODO set socket timeout?
        sock.connect((host_domain, port_num))

        msg = create_torrent_get_request_from_info(host_domain, port_num, base_path, tde, listening_port, peer_id, uploaded = uploaded, downloaded = downloaded, left = left, event = event)

        context = ssl.create_default_context()
        ssl_sock = context.wrap_socket(sock, server_hostname=host_domain)

        try:
            ssl_sock.sendall(msg)
            # receive the response back, the payload of the http response is stored in resp
            resp = recv_http_response(ssl_sock)
        except socket.timeout:
            raise socket.timeout("Timeout when connecting to https tracker")

        return bdecode(resp)


# byte array should be 6 bytes long, in hexadecimal
def extract_ip(byte_arr):
    return str(byte_arr[0]) + "." + str(byte_arr[1]) + "."  + str(byte_arr[2]) + "." + str(byte_arr[3])
    

def extract_port(byte_arr):
    return byte_arr[4] * 256 + byte_arr[5]