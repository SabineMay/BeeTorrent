import socket


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: 
        sock.connect(("127.0.0.1", 1026)) 
    except: 
        print("unsuccessful")
    else: 
        print("yay")
    
    
if __name__=="__main__":
    main()
