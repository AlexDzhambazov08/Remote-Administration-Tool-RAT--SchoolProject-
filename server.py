import socket

HOST = "0.0.0.0"   # слуша на всички мрежови интерфейси
PORT = 5050
ONE_TIME_CODE = "123456"  # за демонстрация

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("Server started")
print("Waiting for connection...")
print("One-time code is:", ONE_TIME_CODE)

conn, addr = server_socket.accept()
print("Connected by:", addr)

data = conn.recv(1024).decode().strip()
print("Received:", data)
print("RAW DATA:", repr(data))

if data == f"CONNECT {ONE_TIME_CODE}":
    conn.sendall("ACCEPT".encode())
    print("Connection accepted")
else:
    conn.sendall("REJECT".encode())
    print("Connection rejected")

conn.close()
server_socket.close()
print("Server closed")
