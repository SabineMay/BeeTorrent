Final project for CMSC417 implementing a BitTorrent client.

Project begun and finished on Github, with intermediate work done in Gitlab.

# 0. Quick start
## Environment setup and takedown
The command-line input we provide here is Mac-specific, but this project should be runnable on Windows and Linux as well
1. Install Python version 3.12 (https://www.python.org/downloads/)
2. Download the wheel file at dist/BeeTorrent-0.1.0-py3-none-any.whl in this repo
3. Create a personal Python venv 
    >```python3 -m venv <venv_name>```
4. Activate <venv_name>
    > ```source <venv_name>/bin/activate```
5. Install the BeeTorrent package into your venv. 
    > ```pip install <local_path>/dist/BeeTorrent-0.1.0-py3-none-any```
6. Do cool torrent-y things
7. Uninstall BeeTorrent if you didn't like it.
    > ```pip uninstall BeeTorrent```
7. Deactivate <venv_name>
    > ```deactivate```

## Starting a torrent
If you've cloned this repo (instead of using the wheel distirubion file), run ```python3 driver.py -f <relative_path_to_torrent_file> -p <desired_port_number>```

If you've installed the package via the distribution file, run ```Dance -f <relative_path_to_torrent_file> -p <desired_port_number>```

Note that -p is optional in both instances (Defaults to 6881). 

BeeTorrent will create two directories, if they don't already exist, wherever you start your torrent: 
1. tor-file-outputs: stores all output files from the torrent 
2. logs: stores automatically generated .log files detailing the peers (Bees) that you've connected to in the swarm

## Debugging/Demonstration Options
* --pa: Specify address to be manually added as a peer
* --pp: Specify port to be manually added as a peer
* --verbose: show the piece download progress and some debug info
* --s: Allow seeding after download is complete

# 1. Supported features
Protocol spec: https://wiki.theory.org/BitTorrentSpecification

## Basic features
* Requests-less communication with HTTP tracker 
* Handshaking with peers
* Support for P2P messages with id $\in$ [0, 1, 2, 3, 4, 6, 7, 8] 
    * keep-alive
    * choke
    * unchoke
    * interested
    * not interested
    * have
    * request
    * piece
    * cancel (we can receive cancels, but see *Known Issues* for discussion around sending them)

## \~Fancy\~ features
* Communication with UDP tracker 
* Communication with HTTPS tracker
* Rarest-first download strategy
* Support for multi-file torrents
* Support for peer messages with id $\in$ [5]
    * bitfield

# 2. Design choices

## High-level decisions
* To handle the number of concurrent TCP connections, we used the standard top-4-unchoke strategy. Every 10 seconds we check who uploaded the most blocks to us (kept track of for each peer) and unchoke them. Before that unchoking everyone but the optimistic unchoke is choked. The optimistic unchoke is grabbed randomly from the swarm every 30s.

* We hard capped piece timeout (where a piece goes from 'requested' to 'ready' so it can be re-requested) at 10s. After running our program with different timeout values, we found that 10s was a happy medium between being too short (causing many retransmissions) and too long (slowing down endgame). See *Experiments*.

* We hard capped the number of outgoing requests per peer to 20. Any value above that and our piece requests began to timeout, indicating that our overwhelmed peers had started dropping requests. The number of requests in flight is controlled by the file I/O, as we wait until after receiving messages to send one request to each and then loop back

* We wanted to minimize the number of file I/O operations (which slow down our program), while implementing the rarest-first download strategy and maintaining functionality for large torrent files. We decided to institute a maximum number of incomplete pieces that our client can store in RAM. Until that maximum has been reached, our client chooses a rare piece from which to send out a block request. Once that maximum has been reached, our client only sends out requests for the in-progress pieces (until the number of incomplete pieces dips below the maximum, at which point we return to rarest-first). The hope is that the client will finish pieces quickly, instead of having a block or two for many incomplete pieces. This provides two benefits: 

1. The client will have more data to upload to peers, leading to more unchokes.
2. The client can wait to write to disk until all the blocks for a piece have come in and can be hash-verified—-if this maximum was not implemented, some other strategy would have to be devised to ensure that a client never overuses its RAM by keeping too many unverified blocks in memory. A large torrent file and bad luck could otherwise crash the program.

    See https://stackoverflow.com/questions/58041609/bittorent-rarest-first-algorithm-how-are-pieces-selected.

* We wanted to make sure that if multiple of our clients were downloading the same torrent, they wouldn't be requesting the same rarest pieces. Per the wikitheory spec: “Note that any Rarest First strategy should include randomization among at least several of the least common pieces, as having many clients all attempting to jump on the same "least common" piece would be counterproductive.” So, after calculating the rarest piece list, we shuffle some of the rarest entries according to a randomly-generated seed. This seed is generated independently for each client instance, lowering the probability that another client will be requesting the same set.

* We wanted to make sure that if a peer's socket failed, we would eventually attempt to reconnect to that peer, in case it started working again. This is why we maintain "dead_swarm"-a list of peers that our connections to have dropped. Occasionally (every 30 seconds or so), we attempt to connect to these peers, and if the connection attempt succeeds, we add it back to the swarm.

## Module decomposition
### State maintenance modules
#### Bee
A class that keeps track of a single peer in the swarm. It maintains:
* The indices of the pieces that the peer has
* A queue of outstanding requests that the peer has made to our client
* The choke and interest relationship between the peer and our client (there are four statuses: (me | peer)(choked | interested))
* The last time our peer sent us a message (inactive peers are disconnected after 2 minutes)

#### Request
A class that keeps track of a single request that a peer has made to our client. Used as an element in the requests queue described in the above Bee class. 

#### PieceList
A class that keeps track of the pieces and blocks that our client wants to or has written to file. Pieces are uniform-length<sup>1</sup>. hash-verifiable fragments of the downloading file. Blocks are uniform-length<sup>2</sup>. subdivisions of pieces for which peers send out request messages.

A piece index is RESOLVED once all its blocks have been received and together hash-verified, and UNRESOLVED otherwise. 

A block index is REQUESTED if our client has sent out a request message for it to at least one peer. A block index is RECEIVED once our client has received a corresponding piece message from a peer. A block index is READY if it has not yet been received, and if our client has not made any outstanding request messages for it.

PieceList also keeps track of request times for each block. Every iteration of the main loop, the driver calls PieceList.set_timedout_requests_to_ready(), which sets blocks that have been REQUESTED more than a set time ago (10 seconds) back to READY, so that they can be REQUESTED again.

Finally, PieceList also contains a dictionary holds the bytes for the incomplete pieces.

<sup>1</sup> Piece length is determined by the metadata specified by the .torrent file. The last piece in a file may be shorter than the others. 

<sup>2</sup> Each client determines its own block length, although there may be size constraints (see the dispute at https://wiki.theory.org/BitTorrentSpecification#request:_.3Clen.3D0013.3E.3Cid.3D6.3E.3Cindex.3E.3Cbegin.3E.3Clength.3E). Peers are responsible, via the slightly-misleadingly-named piece message, for responding with the correctly-sized block. Our client requests blocks of 16000 bytes.

### Tracker messaging modules
#### get_info_from_tracker
Constructs requests for the different types of supported trackers (see "Feature overview") and sends those requests.

This module contains a function, get_info_from_tracker_specified_in_file(), which takes as input the path to a torrent file. It looks through the torrent file for the tracker's address, and uses the proper protocol (udp, http, or https), as specified in the file to contact the tracker and ask it for information on the torrent. It then returns this information as a dictionary to the caller.

#### construct_http_requests
Auxiliary functions for get_info_from_tracker

#### send_receive_message
Decodes a tracker's HTTP response, as well as TCP send/receive functions (see description of same module below)

### Peer messaging modules
#### construct_messages
Constructs messages to be sent to peers

#### handle_messages
Handles the receipt of peer messages. May send responses to peers if prompted (like when receiving a request), but does not contain logic for self-initiated messages (like when generating a request)

#### handshake
Handles intial handshake between peers. When new peers contact you it handles incoming data about the peer

#### download_strat
Calculates the next pieces to request using rarest first strategy according to piecelist.

### Driver module
#### driver
Interfaces all the other modules described in this section: 
* Communicates with tracker
* Creates a bee list with all the peers that connect correctly after handshake
* Creates a piecelist with corresponding length
* Requesting pieces from unchoked peers starting with rarest according to initial bitfields
* Periodically optimistic unchoke and unchoke top 4 peers to handle their requests
* Dispatch any incoming peers 

### Utility modules
#### send_receive_message
Handles basic looping on a TCP socket in order send and receive the expected number of bytes.

#### errors
Largely for handling tcp socket issues like a peer disconnecting without interrupting the overall download

#### arg_parser
Used to parse all the possible input arguments

# 3. Experiments
#### Testing ability to download compared to Transmission client
In order to test speed we picked a couple torrents of different sizes in order to see the difference in speed between our client and Transmission. In order to test this we completed several trials to provide some statistics:
|Statistic                       |Audacity Download Time (s)|Cosmos Download Time(s)|
|--------------------------------|--------------------------|-----------------------|
|Max Time Our Client             |80.87                     |525.18                 |
|Median Time Our Client          |41.51                     |310.22                 |
|Min Time Our Client             |29.5                      |144.16                 |
|Max Time Transmission           |8.31                      |41.61                  |
|Median Time Transmission        |5.275                     |40.8                   |
|Min Time Transmission           |4.73                      |40.23                  |

Audacity Size: 16MB (Testing sample n = 10)
Cosmos Size: 220MB (Testing sample n = 4 using same data for ours as below)

#### Testing ability to upload data
Given that most Torrents will be seeders, we needed a way to show that our clients could upload blocks. In order to show this we developed a seeder option where after downloading the full file we would sit there and seed for incoming connections. In addition we provided the option to hardcode an address and port to ensure connection despite any NAT or firewall weirdness.

We were able to confirm this worked using WireShark to see loopback connection sharing correct pieces.

The video for the below experiment also showcases this functionality.

![lback](demo/lback.png)

#### Testing ability to download a file after communicating with a UDP tracker
The linked video below shows our client communicating with a UDP tracker for initial information before successfully downloading a file.

The client was run in the command line to download the audacity-win-3.7.0-64bit.exe.torrent file, which is the installer for the sound editing software, Audacity. This torrent file announces a UDP tracker, whose URL is printed to the command line and highlighted in the video. 

The video then shows the installer being downloaded through our client in roughly 30 seconds, before the installer is tested and successfully installs Audacity on the host. 

[Link to Demonstration Video](https://youtu.be/k-wyJZWuJnI)

#### Testing ability to download a file after communicating with an HTTPS tracker
The linked video below shows our client communicating with an HTTPS tracker for initial information before successfully downloading a file.

The client was run in the command line to download the rarbg.torrent file, which is a retired database of almost 3,000,000 torrents represented in a SQLite database. This torrent file announces an HTTPS tracker, whose URL is printed to the command line and highlighted in the video. 

The video then shows the database being downloaded through our client in roughly 6 minutes, before a SQLite viewer is used to open the result file and show that it was all downloaded correctly. 

[Link to Demonstration Video](https://youtu.be/y1KFyxLHUGE)

#### Testing ability to download from another instance of our client.
The below video shows that our client can download from another instance of itself.

It first shows us running tcpdump on the docker container's localhost interface in order to capture packets that go between the two instances.

We then ran the client in one terminal window to download Audacity, specifying the --s option so that it seeds after it starts downloading. Once it started seeding, we ran the client in a seperate terminal window, using the --pp and --pa options to get it to connect to the first client.

The video shows us then copying the packet capture file generated by tcpdump to the host windows machine and then opening it up in Wireshark. As one can see, the packet capture shows packets passing back and forth between the two instances.

The video then shows us copying the audacity installer exe to the host windows machine and running it to verify that the file was downloaded correctly (although I didn't run the install through all the way because I had already installed Audacity).

![downloading_from_our_client](demo/videos/downloading_from_our_client.mp4)

#### Testing ability to download from an official client
We used qbittorrent to seed the Audacity torrent. On the same machine, we used our client to download this file (using the --pp and --pa options to manually connect to the qbittorrent instanc). We looked at the qbittorrent download screen and saw our client pop up in the peers list (with our peer id of MD 0.4.1.7) as being uploaded to from qbittorrent, with a non-zero upload rate displayed. We then confirmed that the file (an installer for Audacity) was downloaded correctly by transferring the file out of the docker container that our client was on and using it to install audacity. The following video shows us doing this. 

![downloading_from_official_client](demo/videos/downloading_from_official_client.mp4)


#### Testing the effectiveness of holding incomplete pieces in RAM before writing them to the filesystem.
We hypothesized that the relative slowness of file writing meant that it would be quicker to hold incomplete pieces in RAM (only writing them to the filesystem once the whole piece came in) rather than immediately writing a block to the file once it was received. As explained above, we also included a feature where, if there were greater than a certain number of incomplete pieces (we picked 20), then all requests would be for the incomplete pieces rather than any new ones. We ran a test in which we measured the time it took to download cosmos-laundromat, starting from the end of the initial round of connecting to peers and ending when the file was fully downloaded. To mitigate the effects of inconsistent network performance, we alternated between runs of immediately writing blocks and runs of holding them in RAM. The following results were obtained:

|Run                                    |Time (s)|
|---------------------------------------|--------|
|Holding incomplete pieces in RAM test 1|144.16  |
|Immediately writing blocks test 1      |263.43  |
|Holding incomplete pieces in RAM test 2|266.30  |
|Immediately writing blocks test 2      |399.21  |
|Holding incomplete pieces in RAM test 3|394.15  |
|Immediately writing blocks test 3      |527.66  |
|Holding incomplete pieces in RAM test 4|525.18  |
|Immediately writing blocks test 4      |631.87  |

Although, on average, holding incomplete pieces in RAM was faster, the time it took to download the file increased across the board as the experiment went on, indicating that there was possibly some overriding network factor that dominated the timing results. Still, we chose to keep holding incomplete pieces in RAM, as we reasoned having that less file write operations would be better than having more file write operations.

#### Improving Piece Timeout
We handled timeouts by printing out whenever we received a piece that was in the READY state not the REQUESTED state (this was most likely caused by the request timing out). We tried values from 1-10s and found that anything 5s or less tended to result in a lot of excessive requests and we found 10 to be the most stable with very few repetitions while not providing an abnormal endgame time.

#### Max Pending Requests
Determining the best max pending requests was similar to timeout where it was balancing download speeds with too many repeated requests/slowing down network and testing with many different torrent files/situations. We ran some basic tests that were pretty inconclusive (start to get a lot of repeated requests beginning at 30 so cut off there). They didn't show much between, and we observed that for bigger torrents than this (this was just 16MB) the larger max pending requests showed better performance generally

![mdload](demo/mdload.png)

# 4. Problems encountered and addressed
* Our client is slower than Transmission and qBitTorrent. A few things we attempted in our pursuit of speed include: 
	* Assembling pieces in RAM instead of writing blocks to disk immediately upon receipt. See *Design Decisions* and *Experiments* for further discussion. 
	* Sending requests immediately after receiving a piece. We noticed that our piece-processing loop took up the majority of the running time, so we thought that sending out requests right before entering this loop would increase parallelism. Peers could work on processing our new requests while we did the file I/O that was often necessary to process the pieces we just received. This didn't show much of an improvement in practice.

* Piece and block indices needed to be checked to see if they were the last piece a file or block in a piece, as those lengths could be shorter than normal. 

* Our client does not work on a Ubuntu VM. The flabbergasting thing is, the VM CAN connect to peer sockets, but it never succeeds at doing the BitTorrent handshake with them. Running the client natively allows both to happen. Solution: Abandon the VM. Effectiveness: Frustratingly, very effective. 


# 5. Known issues

## Fatal bugs
* If many instances of our client try to download cosmos-laundromat.torrent, they all stall at 842 pieces (out of 843). If we stop testing and return a few hours later, we can download the entire file once more. Somehow, something in this download has the capacity to be overwhelmed. We wonder if this is related to the ever-increasing download times recorded during RAM vs No-RAM testing in *Experiments*. 

![Magic](demo/magic.png)

* On very rare occasions a client entering has caused an issue trying to handle a piece
outside of the ones we are currently assembling. This generally is fixed by rerunning the program (which also makes it harder to debug)

* Some online torrents don't send us back any peers.

## Performance bugs
* At seemingly random points in a download our client can face a significant reduction in speed before returning back to normal.

* For some of the torrent files where we receive a lot of peers, many of those sockets won’t open (is it possible that they are behind a firewall like us?) and for a few the connection gets reset after the handshake.

## Nonexistance bugs (we didn't implement the feature yet 🙁)
* We don't send out cancel messages once a request times out. 

* We don't send cancel messages during endgame. 

* We don’t attempt to hole-punch through our firewall to our peers. We can initiate a connection to peers advertised by the tracker, but anyone who is not on the machine running our client will fail to initiate a connection to us. 

# 6. Contributors and their contributions

cdavis73 - Calvin Davis
* HTTPS support
* general debugging and testing protocols
* Argument parser
* demo videos (HTTPS + UDP)

pmiller8 - Patrick Miller 
* Handshake protocol
* Top 4 (keeping score) + optimistic unchoking
* download strategy + rarest first
* Documentation + testing
* Seeder mode + upload capability

smay1 - Sabine May
* Peer message handling
* Peer state tracking
* Local piece resolution
* Driver loop
* Documentation + package manifest

ydesilva - Yasadu De Silva
* Tracker HTTP communication + UDP support
* TCP message handling
* Piece request time outs
* Holding pieces in RAM until they need to be written out
* Multi-file output 

