# Decomposiiton
## State maintenance modules
### Bee
A class that keeps track of a single peer in the swarm. It maintains:
* The indices of the pieces that the peer has
* A queue of outstanding requests that the peer has made to our client
* The choke and interest relationship between the peer and our client (there are four statuses: (me | peer)(choked |interested))
* The last time our peer sent us a message (inactive peers are disconnected after TODO minutes)

### Request
A class that keeps track of a single request that a peer has made to our client. Used as an element in the requests queue described in the above Bee class. 

### PieceList
A class that keeps track of the pieces and blocks that our client wants to or has written to file. Pieces are uniform-length<sup>1</sup>. hash-verifiable fragments of the downloading file. Blocks are uniform-length<sup>2</sup>. subdivisions of pieces for which peers send out request messages.

A piece index is RESOLVED once all its blocks have been received and together hash-verified, and UNRESOLVED otherwise. 

A block index is REQUESTED if our client has sent out a request message for it to at least one peer. A block index is RECEIVED once our client has received a corresponding piece message from a peer. A block index is READY if it has not yet been received, and if our client has not made any outstanding request messages for it. 

<sup>1</sup> Piece length is determined by the metadata specified by the .torrent file. The last piece in a file may be shorter than the others. 

<sup>2</sup> Each client determines its own block length, although there may be size constraints (see the dispute at https://wiki.theory.org/BitTorrentSpecification#request:_.3Clen.3D0013.3E.3Cid.3D6.3E.3Cindex.3E.3Cbegin.3E.3Clength.3E). Peers are responsible, via the slightly-misleadingly-named piece message, for responding with the correctly-sized block. Our client requests blocks of 16000 bytes.

## Tracker messaging modules
### get_info_from_tracker
Constructs requests for the different types of supported trackers (see "Feature overview") and sends those requests.

### construct_http_requests
Auxiliary functions for get_info_from_tracker

### send_receive_message
Decodes a tracker's HTTP response

## Peer messaging modules
### construct_messages
Constructs messages to be sent to peers

### handle_messages
Handles the receipt of peer messages. May send responses to peers if prompted (like when receiving a request), but does not contain logic for self-initiated messages (like when generating a request)

### download_strat
Calculates the next pieces to request using rarest first strategy.

## Driver module
### driver
It drives.

## Utility modules
### send_receive_message
Handles basic looping on a TCP socket in order send and receive the expected number of bytes.

### errors
Errors :/

# Who’s doing what
Patrick 
* Handshake protocol
* Top 4 (keeping score) + optimistic unchoking
* download strategy - rarest first

Yasadu
* Tracker communication + UDP support
* TCP message handling
* Download efficiency
* Multi-file output 

Sabine
* Peer message handling
* Peer state tracking
* Local piece resolution
* Driver loop

Calvin
* HTTPS support
* general debugging and testing protocols


# Tentative testing scheme
* Compare speed of download with qbittorrent/transmission example clients by running both on the same torrent file and record how long each takes to download
* Run multiple of our clients on the same torrent file at the same time and use wireshark to ensure messages are being passed between
* Find torrents with more leechers to run our client to optimize speed with other clients in process of downloading

# EC plans + progress
* Communication with UDP tracker – in progress, dealing with bug where terminal hangs while receiving tracker response
* Communication with HTTPS tracker – in progress
* Rarest-first download strategy – done in theory, but likely needs some more testing with torrents that have more leeches (most of our existing tests have been largely seeders)
* Support for multi-file torrents – done

