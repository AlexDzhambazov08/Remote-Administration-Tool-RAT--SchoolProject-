import socket
import threading
import cv2
import pickle
import struct
from pynput import mouse, keyboard

SERVER_IP = input("Enter server IP: ")
PORT_CMD = 5050
PORT_VID = 5051
code = input("Enter one-time code: ").strip()

# cmd channel connection
cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cmd_socket.connect((SERVER_IP, PORT_CMD))
cmd_socket.sendall(f"CONNECT {code}".encode())

if cmd_socket.recv(1024).decode() != "ACCEPT":
    print("Authentication failed!")
    exit()

# vid channel connection
vid_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
vid_socket.connect((SERVER_IP, PORT_VID))

remote_control_active = False
# prevents concurrent sendall() calls from different threads
send_lock = threading.Lock()

def safe_send(data: bytes):
    with send_lock:
        try:
            cmd_socket.sendall(data)
        except Exception as e:
            print(f"Send error: {e}")

def on_move(x, y):
    if remote_control_active:
        safe_send(f"MOVE {int(x)} {int(y)}\n".encode())

def on_click(x, y, button, pressed):
    if remote_control_active and pressed:
        btn_name = str(button).split('.')[-1].lower()
        safe_send(f"MOUSE {int(x)} {int(y)} {btn_name}\n".encode())

def on_scroll(x, y, dx, dy):
    if remote_control_active:
        safe_send(f"SCROLL {int(x)} {int(y)} {int(dy)}\n".encode())

def on_press(key):
    global remote_control_active
    if key == keyboard.Key.f8:
        remote_control_active = not remote_control_active
        print(f"\n[!] Remote Control: {'ON' if remote_control_active else 'OFF'}")
        return
    if remote_control_active:
        k = key.char if hasattr(key, 'char') and key.char else str(key).replace("Key.", "")
        safe_send(f"KEY {k}\n".encode())

# reads server replies (/help, /stop, etc.)
def response_reader_thread():
    while True:
        try:
            response = cmd_socket.recv(4096).decode().strip()
            if response:
                print(f"\n[Server] {response}")
                print("Terminal > ", end="", flush=True)
        except Exception:
            break

# Terminal input thread
def terminal_input_thread():
    while True:
        try:
            cmd = input("\nTerminal > ").strip()
            if cmd:
                safe_send(cmd.encode())
        except EOFError:
            break

# Start background threads
threading.Thread(target=response_reader_thread, daemon=True).start()
threading.Thread(target=terminal_input_thread, daemon=True).start()
mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll).start()
keyboard.Listener(on_press=on_press).start()

# Main video cycle
print("\n--- CONNECTED ---")
print("Initializing video window...")
print("Press 'F8' to toggle remote mouse and keyboard control.")
print("Press 'F' for fullscreen")
print("Press 'ESC' to exit.")
print("Type '/help' below for text commands.")

cv2.namedWindow("Remote Screen", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Remote Screen", cv2.WND_PROP_ASPECT_RATIO, cv2.WINDOW_FREERATIO)

payload_size = struct.calcsize("Q")
data = b""

try:
    while True:
        while len(data) < payload_size:
            packet = vid_socket.recv(4096)
            if not packet:
                break
            data += packet
        if not data:
            break

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data) < msg_size:
            data += vid_socket.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = cv2.imdecode(pickle.loads(frame_data), cv2.IMREAD_COLOR)
        cv2.resizeWindow("Remote Screen", 1680, 1050)
        cv2.imshow("Remote Screen", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC to exit
            break
        elif key == ord('f'):  # F to toggle fullscreen
            is_fullscreen = cv2.getWindowProperty("Remote Screen", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(
                "Remote Screen",
                cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_NORMAL if is_fullscreen == cv2.WINDOW_FULLSCREEN else cv2.WINDOW_FULLSCREEN
            )
except Exception as e:
    print(f"Connection error: {e}")
cv2.destroyAllWindows()