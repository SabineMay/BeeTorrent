from construct_http_requests import *
from bcoding import bencode, bdecode
import hashlib
import urllib.parse
import socket
from send_receive_message import *
from random import randint

NETWORK_ORDER = 'big'
MAGIC_NUMBER_UDP = 0x41727101980

def create_torrent_get_request_from_file(torrent_file_path, listening_port, uploaded = 0, downloaded = 0, left = None, event = None):
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
   
    # temporary while we figure out what peer id to use
    # TODO figure this out
    params['peer_id'] = params['info_hash']

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

def perform_udp_tracker_protocol(sock, torrent_file_path, listening_port, uploaded = 0, downloaded = 0, left = None, event = None):
    torfile = open(torrent_file_path, 'rb')
    tde = bdecode(torfile)
    
    host_domain = (tde['announce'].replace("udp://", "")).split(":")[0]
    port_number = 0

    # get port number from torrent file
    if ("/" in (tde['announce'].replace("udp://", "")).split(":")[1]):
        port_number = int((tde['announce'].replace("udp://", "")).split(":")[1].split("/")[0])
    else:
        port_number = int((tde['announce'].replace("udp://", "")).split(":")[1])

    transaction_id = rand_transaction_id()

    connect_request = create_udp_connect_request(transaction_id)

    sock.sendto(connect_request, (host_domain, port_number))

    




# function that returns tuple of ((tracker domain, tracker port), metadata from tracker)
def get_info_from_tracker_specified_in_file(torrent_file_path, listening_port, uploaded = 0, downloaded = 0, left = None, event = None):
    torfile = open(torrent_file_path, 'rb')
    tde = bdecode(torfile)

    if "http://" in tde['announce']:
        # get host domain from torrent file
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
        msg = create_torrent_get_request_from_file(torrent_file_path, listening_port, uploaded = uploaded, downloaded = downloaded, left = left, event = event)
        send_message_tcp(msg, sock)

        # receive the response back, the payload of the http response is stored in resp
        resp = recv_http_response(sock)

        # decode and return
        return bdecode(resp)
    elif "udp://" in tde['announce']:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        tracker_info = perform_udp_tracker_protocol(sock, torrent_file_path, listening_port, uploaded = uploaded, downloaded = downloaded, left = left, event = event)

        # decode and return
        return bdecode(resp)

    

