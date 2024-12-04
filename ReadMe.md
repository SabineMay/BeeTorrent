# Project overview
## Description
Final project for CMSC417 implementing a BitTorrent client.

## Language and libraries
Language: Python (Version 3.12)\
External libraries: bcoding

## Contributors
cdavis73 - Calvin Davis\
pmiller8 - Patrick Miller\
smay1 - Sabine May\
ydesilva - Yasadu De Silva

# Quick start
## Environment setup and takedown
The command-line input we provide here is Mac-specific, but this project should be runnable on Windows and Linux as well
1. Install Python version 3.12 (https://www.python.org/downloads/)
2. Clone this repo onto your machine
3. Create a personal Python venv within your local repo
    >```python3 -m venv <venv_name>```
4. Activate <venv_name>
    > ```source <venv_name>/bin/activate```
5. Install bcoding library within <venv_name>
    > ```pip install bcoding```
6. Do cool torrent-y things
7. Deactivate <venv_name>
    > ```deactivate```
    
## Starting a torrent
TODO: Describe command line arguments that the user should provide, the directory that there torrent files should be located in, and give an example command. 

## Jupyter demo
TODO: Link a jupyter file and PDF with its saved output where we show the program working with a given torrent file (ideally a multifile, maybe cosmos-laundromat or something). This is a good backup in case something goes wrong the day of the demonstration.


# Feature overview
Protocol spec: https://wiki.theory.org/BitTorrentSpecification

## Basic features
* Requests-less communication with HTTP tracker 
* Handshaking with peers
* Support for peer messages with id $\in$ [0, 1, 2, 3, 4, 6, 7, 8] 
    * keep-alive
    * choke
    * unchoke
    * interested
    * not interested
    * have
    * request
    * piece
    * cancel

## ~Fancy~ features
* Communication with UDP tracker 
* Communication with HTTPS tracker
* Rarest-first download strategy
* Support for multi-file torrents
* Support for peer messages with id $\in$ [5]
    * bitfield

## Open issues
TODO: talk about maintaining requests queue vs outright rejecting request, link queing debate from the wiki: https://wiki.theory.org/BitTorrentSpecification#Queuing 

## Future work
* Implement support for peer messages with id $\in$ [9]
    * port (used in BT-DHT)

* Keep blocks in RAM until the whole piece has been hash-verified. Right now we are writing each (unverified) block to file, and then retrieving them upon receipt of the last block in a piece. This is less efficient, and means the file is only guaranteed to be correct after the torrent finishes -- we erase blocks from the file if we if the hash fails once the last block in a piece has been received. 

# Module overview
## State maintenance
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

## Tracker messaging
### get_info_from_tracker
Constructs requests for the different types of supported trackers (see "Feature overview") and sends those requests.

### construct_http_requests
Auxiliary functions for get_info_from_tracker

### send_receive_message
Decodes a tracker's HTTP response

## Peer messaging
### construct_messages
Constructs messages to be sent to peers

### handle_messages
Handles the receipt of peer messages. May send responses to peers if prompted (like when receiving a request), but does not contain logic for self-initiated messages (like when generating a request)

### download_strat
TODO

## Driver
### driver
It drives.

## Utility
### send_receive_message
Handles basic looping on a TCP socket in order send and receive the expected number of bytes.

### errors
Errors :/


