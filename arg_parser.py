import sys
from ipaddress import ip_address

_verbose = False

# print if --verbose specified
def vlog(message):
    if _verbose:
        print(message)

def arg_parse(argv: list[str]):
    seeding = False
    # These are the possible command line arguments that we have support for
    possible_options = ["-p", "--verbose", "-h", "-f", "--pa", "--pp"]

    expected_argv_length = 1

    port = 6881
    torfile_path = ""
    err = False
    # Note that every error catch checks "if not err"; this is so only one error message is printed
    # and doesn't bombard users with all error messages.

    print() # space for readability

    # -h: help (ALL OTHER ARGUMENT PROCESSING MUST GO BELOW THIS ONE)
    # This is so -h basically just overrides any other arguments and prints the usage rather than running the code.
    if "-h" in argv:
        help_message = """Command usage:
-f [filename]: specify torrent file to download [required]
-p [port]: specify port to run on, 6881 if not provided [optional]
-h: see command usage
--verbose: enable verbose logging (for debug purposes), default false
"""
        print(help_message)
        exit(0)

    # -f: Specify the torrent file to work with
    if "-f" in argv:
        expected_argv_length += 2
        arg_loc = argv.index("-f")
        try:
            torfile_path = argv[arg_loc + 1] # out of bounds if -f was specified but nothing was given with it, if it was last arg given
            if torfile_path in possible_options:
                raise IndexError # meaning that -f was specified but nothing was given with it
        except IndexError:
            if not err:
                print("Invalid arguments: -f option specified but no filepath given.", file=sys.stderr)
                err = True
    else:
        if not err:
            print("Invalid arguments: torrent file not specified. Use -f option to specify file.", file=sys.stderr)
            err = True
    
    # -p: Specify the port to work on.
    if "-p" in argv:
        expected_argv_length += 2
        arg_loc = argv.index("-p")
        try:
            port = argv[arg_loc + 1]
            if port in possible_options:
                raise IndexError
            port = int(port)
        except IndexError:
            if not err:
                print("Invalid arguments: -p option specified but no port given.", file=sys.stderr)
                err = True
        except ValueError:
            if not err:
                print("Invalid arguments: non-integer port provided.", file=sys.stderr)
                err = True
   
    peer_port = -1
    peer_ip = ""
    # --pp: specify the port of a peer
    if "--pp" in argv:
        expected_argv_length += 2
        arg_loc = argv.index("--pp")
        try:
            peer_port = argv[arg_loc + 1]
            if peer_port in possible_options:
                raise IndexError
            peer_port = int(peer_port)
        except IndexError:
            if not err:
                print("Invalid arguments: --pp option specified but no port given.", file=sys.stderr)
                err = True
        except ValueError:
            if not err:
                print("Invalid arguments: non-integer port provided.", file=sys.stderr)
                err = True
    
    if "--pa" in argv:
        expected_argv_length += 2
        arg_loc = argv.index("--pa")
        try:
            peer_ip = argv[arg_loc + 1]
            if peer_ip in possible_options:
                raise IndexError
            ip_address(peer_ip)
        except IndexError:
            if not err:
                print("Invalid arguments: --pa specified but no ip given")
                err = True
        except ValueError:
            if not err:
                print("Invalid arguments: non-ip provided", file = sys.stderr)
                err = True

    # --verbose: Enable debug logging.
    if "--verbose" in argv:
        expected_argv_length += 1
        global _verbose
        _verbose = True

    # --verbose: Enable debug logging.
    if "--s" in argv:
        expected_argv_length += 1
        seeding = True


    # If we got unexpected arguments
    if len(argv) != expected_argv_length:
        if len(argv) > expected_argv_length:
            if not err:
                print("Invalid arguments: Unknown arguments provided.", file=sys.stderr)
                err = True
        else:
            # I don't think this is possible but redundancy is good
            if not err:
                print("Invalid arguments: Incomplete arguments provided.", file=sys.stderr)
                err = True

    if err:
        print("Run \"python3 driver.py -h\" to see command usage.", file=sys.stderr)
        print() # for readability
        exit(1)

    return (port, torfile_path, (peer_ip, peer_port), seeding)