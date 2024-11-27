from construct_http_requests import *
from bcoding import bencode, bdecode
import hashlib

def create_torrent_get_request_from_file(torrent_file_path):
    torfile = open(torrent_file_path, 'rb')
    tde = bdecode(torfile)

    host_name = (tde['announce'].replace("udp://", "")).split(":")[0]
    port_number = 0
    base_path = ""

    # sometimes the announce address doesn't specify a path, so we assume it's /announce
    if ("/" in (tde['announce'].replace("udp://", "")).split(":")[1]):
        port_number = int((tde['announce'].replace("udp://", "")).split(":")[1].split("/")[0])
        base_path = "/" + (tde['announce'].replace("udp://", "")).split("/")[1]
    else:
        port_number = int((tde['announce'].replace("udp://", "")).split(":")[1])
        base_path = "/announce"

    h = hashlib.sha1()

    h.update(bencode(tde['info']))

    print(h.digest())

    

    '''
    addrstr = tde['announce']
    addrsep = addrstr.split(':')
    ip_addr = addrsep[0] + addrsep[1]
    port = addrsep[2]
    '''

    