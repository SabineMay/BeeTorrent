import socket


def main():
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.bind(("0.0.0.0", 1026)) 
    listen_sock.listen(5)
    print(listen_sock.accept())
    
    

if __name__=="__main__":
    main()
