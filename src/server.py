import threading
import time
import socket
import os
from datetime import datetime

class Server:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 12345
        self.clients = {}
        self.dir_path = "Server Files"
        self.create_dir()
        self.start()
            
    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((self.host, self.port))
            server.listen(5)
            print("Starting server on port:", self.port)
            
            while True:
                client, addr = server.accept()
                print(f"[{datetime.now()}] {addr} has connected to the server")
                thread = threading.Thread(target=self.handle_client, args=(client, addr))
                thread.start()
                
    def handle_client(self, client, addr):
        with client:
            writer = client.makefile('w')
            reader = client.makefile('r')
            handle = None
            try:
                writer.write("Connection to the File Exchange Server is successful!\n")
                writer.flush()
                
                while True:
                    client_input = reader.readline().strip()
                    if not client_input:
                        break
                    
                    print(f"[{datetime.now()}] Received command from {addr}: {client_input}")
                    commands = client_input.split(" ")
                    instruc = commands[0]
                    
                    if not handle and (instruc != '/register'):
                        writer.write("Error: Registration required. Please register first.\n")
                        writer.flush()
                    elif instruc == '/register' and not handle:
                        handle = self.register(commands, writer)
                    else:
                        if instruc == "/join":
                            writer.write("Already joined the server!\n")
                            writer.flush()
                        elif instruc == "/leave":
                            self.disconnect(writer, handle)
                            break
                        elif instruc == "/get":
                            writer.write("OK\n")
                            writer.flush()
                            self.get_file(commands, writer, client, handle)
                        elif instruc == "/store":
                            writer.write("OK\n")
                            writer.flush()
                            self.handle_store(commands, writer, client, handle)
                        elif instruc == "/dir":
                            writer.write("OK\n")
                            writer.flush()
                            self.dir_files(writer)
                        elif instruc == "/?":
                            self.ask_help(writer)
                        else:
                            writer.write("Error: Command not found.\n")
                            writer.flush()
            except Exception as e:
                writer.write(f"Error: {e}\n")
                writer.flush()
            finally:
                if handle:
                    self.clients.pop(handle.lower(), None)
                    print(f"[{datetime.now()}] {handle} has disconnected")
                client.close()
                
    def register(self, commands, writer):
        if len(commands) == 2:
            handle = commands[1]
            if handle.lower() not in self.clients:
                self.clients[handle.lower()] = writer
                welcome_message = f"Welcome {handle}!\n"
                writer.write(welcome_message)
                writer.flush()
                print(f"[{datetime.now()}] Handle registered: {handle}")
                return handle
            else:
                writer.write("Error: Registration failed. Handle or alias already exists.\n")
                writer.flush()
        else:
            writer.write("Error: Invalid command syntax for /register.\n")
            writer.flush()
        return None
    
    def create_dir(self):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
            print(f"Directory successfully created: {self.dir_path}")
            
    def dir_files(self, writer):
        files = os.listdir(self.dir_path)
        if files:
            file_list = "\n".join(files)
        else:
            file_list = "No files available."
        writer.write(f"<SOM>\nServer Directory\n{file_list}\n<EOM>\n")
        writer.flush()
        print(f"[{datetime.now()}] Sent directory list to client")

    def disconnect(self, writer, handle):
        if handle:
            self.clients.pop(handle.lower(), None)
            writer.write("Connection closed. Thank you!\n")
            print(f"[{datetime.now()}] {handle} has disconnected")
        else:
            writer.write("Error: Disconnection failed. Please connect to the server first.\n")
        writer.flush()

    def handle_store(self, commands, writer, client, handle):
        if len(commands) < 2:
            writer.write("Error: Filename missing\n")
            writer.flush()
            return

        filename = commands[1]
        path = os.path.join(self.dir_path, filename)
        
        try:
            with open(path, 'wb') as file:
                print(f"[{datetime.now()}] Storing file {filename} from {handle}")
                while True:
                    data = client.recv(4096)
                    if not data or data.endswith(b"<EOF>"):  # Detect end of file marker
                        if data.endswith(b"<EOF>"):
                            data = data[:-5]  # Remove EOF marker
                        file.write(data)
                        break
                    file.write(data)
                file.flush()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                upload_message = f"{handle}<{timestamp}>: Uploaded {filename}\n"
                print(upload_message)
                writer.write(upload_message)
                writer.flush()
        except Exception as e:
            writer.write(f"Error storing file: {e}\n")
            writer.flush()
 
    def get_file(self, commands, writer, client, handle):
        if len(commands) < 2:
            writer.write("Error: Enter a filename.\n")
            writer.flush()
            return

        filename = commands[1]
        path = os.path.join(self.dir_path, filename)

        if not os.path.isfile(path):
            writer.write("Error: File not found in the server.\n")
            writer.flush()
            return

        file_size = os.path.getsize(path)
        writer.write(f"{file_size}\n")
        writer.flush()

        # Delay the sending of file
        time.sleep(1)

        try:
            with open(path, 'rb') as file:
                while chunk := file.read(4096):
                    client.sendall(chunk)
                client.sendall(b"<EOF>")  # Send EOF marker
            print(f"File {filename} sent to {handle}")
        except Exception as e:
            writer.write(f"Error sending file: {e}\n")
            writer.flush()

    def ask_help(self, writer):
        help_message = (
            "<SOM>Available commands: \n"
            "/join <server_ip> <port> - Connect to the server\n"
            "/leave - Disconnect from the server\n"
            "/register <handle> - Register a unique handle\n"
            "/store <filename> - Send file to server\n"
            "/dir - List files on server\n"
            "/get <filename> - Fetch file from server\n"
            "/? - Show this help message<EOM>\n"
        )
        writer.write(help_message)
        writer.flush()

# If this file is running, make it main and start the server.        
if __name__ == "__main__":
    server = Server()
