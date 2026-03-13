import socket
import mss
import cv2
import numpy as np
import pickle
import struct
import threading
import pyautogui

SERVER_IP = input("Server IP: ")
PORT = 5050
CODE = input("Code: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP,PORT))

client.send(f"CONNECT {CODE}".encode())

response = client.recv(1024).decode()

if response != "ACCEPT":
    print("Rejected")
    exit()

print("Connected")

def send_screen():

    with mss.mss() as sct:

        monitor = sct.monitors[1]

        while True:

            img = sct.grab(monitor)
            frame = np.array(img)

            frame = cv2.resize(frame,(1280,720))

            result,encoded = cv2.imencode(
                ".jpg",
                frame,
                [cv2.IMWRITE_JPEG_QUALITY,60])

            data = pickle.dumps(encoded)

            message = struct.pack("Q",len(data))+data

            try:
                client.sendall(message)
            except:
                break

def command_listener():

    while True:

        try:

            msg = client.recv(1024)

            if not msg:
                break

            msg = msg.decode()

            parts = msg.split()

            if parts[0] == "MOVE":

                x=int(parts[1])
                y=int(parts[2])

                pyautogui.moveTo(x,y)

            elif parts[0] == "MOUSE":

                x=int(parts[1])
                y=int(parts[2])

                pyautogui.click(x,y)

            elif parts[0] == "SCROLL":

                pyautogui.scroll(int(parts[2]))

            elif parts[0] == "KEY":

                pyautogui.press(parts[1])

            elif parts[0] == "FILE":

                size=int(parts[1])

                data=b""

                while len(data)<size:
                    data+=client.recv(4096)

                with open("received_file","wb") as f:
                    f.write(data)

                print("File received")

            elif parts[0] == "EXIT":
                break

        except:
            break

screen_thread = threading.Thread(target=send_screen)
command_thread = threading.Thread(target=command_listener)

screen_thread.start()
command_thread.start()

screen_thread.join()
command_thread.join()

client.close()
