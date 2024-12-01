from send_receive_message import *

def keep_alive(sock):
    mes = bytearray(4)
    send_message_tcp(mes, sock)

def choke(sock):
    mes = bytearray(5)
    mes[3] = 1
    send_message_tcp(mes, sock)

def unchoke(sock):
    mes = bytearray(5)
    mes[3] = 1
    mes[4] = 1
    send_message_tcp(mes, sock)

def interested(sock):
    mes = bytearray(5)
    mes[3] = 1
    mes[4] = 2
    send_message_tcp(mes, sock)

def not_interested(sock):
    mes = bytearray(5)
    mes[3] = 1
    mes[4] = 1
    send_message_tcp(mes, sock)