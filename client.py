import socket

SERVER_IP = input("Enter server IP: ")
PORT = 5050
code = input("Enter one-time code: ").strip()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

message = f"CONNECT {code}"
client_socket.sendall(message.encode())

response = client_socket.recv(1024).decode()
print("Server response:", response)

client_socket.close()
