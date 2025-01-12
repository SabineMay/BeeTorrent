Documentation:
* delete README.md and replace with final-report.md
* tag final-report.md
* make things runnable on command line with user input

Code:
* TODO: verify no runtime errors for one peer can crash the whole program
* setup bitmap and send that to peers upon handshake
* need to talk to the tracker periodically, not just once at the beginnig -- has something to do with the interval field I think
* verify that we are properly using %nn escaping for peerid and infohash --> could this be related to why some peers are dropping our connection?

* DONE: make sure we are prioritizing pieces for which we already have a few blocks downloaded before starting new pieces
* DONE: make sure commands work with directory structure/where torrent files are located
* DONE: pass peerid calculated at beginning of main into create_torrent_get_request_from_file so that we can send it into tracker
