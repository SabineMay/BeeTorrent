from construct_http_requests import *
from bcoding import bencode, bdecode
import hashlib
import urllib.parse

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
