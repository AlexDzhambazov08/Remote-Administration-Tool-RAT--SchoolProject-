import socket

HOST = "0.0.0.0"   # слуша на всички мрежови интерфейси
PORT = 5050
ONE_TIME_CODE = "123456"  # за демонстрация

# Custom commands here - format: command: response (save before running file)
COMMANDS = {
    ("/exit", "exit"): "Exit the server.", # Both /exit and exit are work in progress work
    ("/help"): "Display all commands.",
    ("/67"): "Six seveeeeeeen!",
    ("/stop"): "Stopping the server..."
}

# Main server loop
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("Server started")
print("Waiting for connection...")
print("One-time code is:", ONE_TIME_CODE)

server_running = True
while server_running:
    conn, addr = server_socket.accept()
    print("Connected by:", addr)

    data = conn.recv(1024).decode().strip()
    print("Received:", data)
    print("RAW DATA:", repr(data))

    if data == f"CONNECT {ONE_TIME_CODE}":
        conn.sendall("ACCEPT".encode())
        print("Connection accepted")
        
        while True:
            try:
                command = conn.recv(1024).decode().strip()
                
                if not command:
                    break
                
                print("Received command:", command)
                
                if command in COMMANDS:
                    if command == "/stop":
                        conn.sendall("Server is stopping...".encode())
                        print("Stopping server...")
                        server_running = False
                        break
                    
                    elif command == "/exit" or command == "exit":
                        conn.sendall("Goodbye!".encode())
                        print("Client disconnected")
                        break

                    # If its help command, send the list of available commands
                    elif command == "/help":
                        help_text = "Available commands:\n" + "\n".join(f"{cmd}: {resp}" for cmd, resp in COMMANDS.items())
                        conn.sendall(help_text.encode())
                    
                    else:
                        conn.sendall(COMMANDS[command].encode())

                else:
                    conn.sendall(f"Executed: {command}".encode())
            
            except Exception as e:
                print("Connection error:", e)
                break
    else:
        conn.sendall("REJECT".encode())
        print("Connection rejected")
    
    conn.close()
    if not server_running:
        break

server_socket.close()
print("Server closed")
