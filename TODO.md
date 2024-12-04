* make sure we are prioritizing pieces for which we already have a few blocks downloaded before startig new pieces
* need to talk to the tracker periodically, not just once at the beginnig -- has something to do with the interval field I think

For checkpoint documentation:
* make things runnable on command line with user input
* make sure commands work with directory structure/where torrent files are located



* get rid of raise runtime errors in things like send_msg_tcp bc we don't want entire program to fail during demonstration if one peer gets dropped
* pass peerid calculated at beginning of main into create_torrent_get_request_from_file so that we can send it into tracker
* verify that we are properly using %nn escaping for peerid and infohash --> could this be related to why some peers are dropping our connection?
* setup bitmap and send that to peers upon handshake