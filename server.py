import socket
import threading
import cv2
import numpy as np
import pickle
import struct
import mss
import pyautogui

HOST = "0.0.0.0"   # слуша на всички мрежови интерфейси
PORT_CMD = 5050
PORT_VID = 5051
ONE_TIME_CODE = "123456"  # за демонстрация

# Custom commands here - format: command: response (save before running file)
COMMANDS = {
    "/exit" : "Exit the server.",
    "/help": "Display all commands.",
    "/67": "Six seveeeeeeen!",
    "/stop": "Stopping the server..."
}

def send_screen(vid_conn):
    """Continuously grabs the screen and sends it to the Admin via the Video Port."""
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            try:
                img = sct.grab(monitor)
                frame = np.array(img)
                # Mac colors: Convert BGRA to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                h, w = frame.shape[:2]

                # If the screen is huge (4k), scale it down to 1080p equivalent
                scale = 1920 / w if w > 1920 else 1
                new_w, new_h = int(w * scale), int(h * scale)

                # INTER_AREA is a special filter that makes resizing look sharper
                frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
                result, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

                data = pickle.dumps(encoded)
                message = struct.pack("Q", len(data)) + data
                vid_conn.sendall(message)
            except Exception as e:
                print(f"Screen stream stopped: {e}")
                break

# cmd socket
cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cmd_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
cmd_socket.bind((HOST, PORT_CMD))
cmd_socket.listen(1)

# vid socket
vid_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
vid_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
vid_socket.bind((HOST, PORT_VID))
vid_socket.listen(1)

print("Server started")
print(f"Waiting for connection... (Code: {ONE_TIME_CODE})")

cmd_conn, addr = cmd_socket.accept()
print(f"Command Channel Connected by: {addr}")

# Auth
auth_data = cmd_conn.recv(1024).decode().strip()
if auth_data == f"CONNECT {ONE_TIME_CODE}":
    cmd_conn.sendall("ACCEPT".encode())

    # Waits for auth then accepts vid connection
    vid_conn, vid_addr = vid_socket.accept()
    print("Video Channel Connected.")

    # Send screen in the background
    threading.Thread(target=send_screen, args=(vid_conn,), daemon=True).start()

    # cmd loop
    server_running = True
    while server_running:
        try:
            raw_data = cmd_conn.recv(1024).decode().strip()
            if not raw_data:
                break

            # Handle Custom Text Commands (Starting with '/')
            if raw_data.startswith("/"):
                print(f"Terminal Command: {raw_data}")
                if raw_data in ("/stop", "/exit"):
                    cmd_conn.sendall("Server is stopping...".encode())
                    server_running = False
                elif raw_data == "/help":
                    help_text = "Available commands:\n" + "\n".join(f"{k}: {v}" for k, v in COMMANDS.items())
                    cmd_conn.sendall(help_text.encode())
                elif raw_data in COMMANDS:
                    cmd_conn.sendall(COMMANDS[raw_data].encode())
                else:
                    cmd_conn.sendall(f"Unknown command: {raw_data}".encode())

            # Handle Remote Control Commands (MOVE, KEY, MOUSE, SCROLL)
            else:
                parts = raw_data.split()
                if not parts:
                    continue

                if parts[0] == "MOVE":
                    pyautogui.moveTo(int(parts[1]), int(parts[2]))
                elif parts[0] == "MOUSE":
                    pyautogui.click(int(parts[1]), int(parts[2]))
                elif parts[0] == "SCROLL":
                    # Format sent by client: "SCROLL <x> <y> <dy>"
                    pyautogui.scroll(int(parts[3]), x=int(parts[1]), y=int(parts[2]))
                elif parts[0] == "KEY":
                    pyautogui.press(parts[1])

        except Exception as e:
            print("Connection error:", e)
            break

else:
    cmd_conn.sendall("REJECT".encode())
    print("Connection rejected")

cmd_conn.close()
cmd_socket.close()
vid_socket.close()
print("Server closed")