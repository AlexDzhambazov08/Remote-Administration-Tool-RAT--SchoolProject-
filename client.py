import socket
import sys

SERVER_IP = sys.stdin.readline().strip()# input("Enter server IP: ")
PORT = 5050
code = sys.stdin.readline().strip()# input("Enter one-time code: ").strip()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

message = f"CONNECT {code}"
client_socket.sendall(message.encode())

response = client_socket.recv(1024).decode()
print("Server response:", response, flush=True)

# Enter command loop
if response == "ACCEPT":
    try:
        while True:
            cmd = sys.stdin.readline().strip()# input("Enter command (use '/exit' or 'exit' to quit): ").strip()
            
            if not cmd:
                continue
            client_socket.sendall(cmd.encode())
            
            if cmd == "/exit" or cmd == "exit":
                client_socket.shutdown(socket.SHUT_RDWR)
                
            # Wait for server reply
            reply = client_socket.recv(1024).decode()
            print("Server reply:", reply, flush=True)
    
    except (ConnectionResetError, BrokenPipeError):
        print("Connection closed by server.")

else:
    print("Authentication failed, closing client.")

client_socket.close()
