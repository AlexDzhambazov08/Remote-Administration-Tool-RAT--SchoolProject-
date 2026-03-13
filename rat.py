import socket
import threading
import cv2
import pickle
import struct
import numpy as np
from pynput import mouse, keyboard

HOST = "0.0.0.0"
PORT = 5050
CODE = "123456"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("Server started")
print("Code:", CODE)

conn, addr = server.accept()
print("Connected:", addr)

data = conn.recv(1024).decode()

if data != f"CONNECT {CODE}":
    conn.send(b"REJECT")
    conn.close()
    exit()

conn.send(b"ACCEPT")

payload_size = struct.calcsize("Q")
data = b""

def receive_screen():

    global data

    while True:

        while len(data) < payload_size:
            packet = conn.recv(4096)
            if not packet:
                return
            data += packet

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data) < msg_size:
            data += conn.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data)
        frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        cv2.imshow("Remote Screen", frame)

        if cv2.waitKey(1) == 27:
            break

def send_mouse(x,y,button,pressed):

    msg = f"MOUSE {x} {y} {button} {pressed}"
    conn.send(msg.encode())

def on_move(x,y):
    conn.send(f"MOVE {x} {y}".encode())

def on_click(x,y,button,pressed):
    send_mouse(x,y,str(button),pressed)

def on_scroll(x,y,dx,dy):
    conn.send(f"SCROLL {dx} {dy}".encode())

def on_press(key):

    try:
        conn.send(f"KEY {key.char}".encode())
    except:
        conn.send(f"KEY {key}".encode())

def send_file():

    path = input("File path to send: ")

    try:
        with open(path,"rb") as f:
            data = f.read()

        header = f"FILE {len(data)}".encode()
        conn.send(header)

        conn.sendall(data)

        print("File sent")

    except:
        print("Failed sending file")

screen_thread = threading.Thread(target=receive_screen)
screen_thread.start()

mouse_listener = mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=on_scroll)

keyboard_listener = keyboard.Listener(on_press=on_press)

mouse_listener.start()
keyboard_listener.start()

while True:

    cmd = input("server command (/file /exit): ")

    if cmd == "/file":
        send_file()

    if cmd == "/exit":
        conn.send(b"EXIT")
        break

conn.close()
server.close()
