import threading
import time
import socket
from datetime import datetime
import os

class Server :
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 12345
        self.clients = {}
        self.dir_path = "Server Files"
        self.create_dir()
        self.start()
            
    # Start the server
    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            # Bind the IP address and port to the server
            # Make the server start listening up
            server.bind((self.host, self.port))
            server.listen(5)
            print("Starting the server on port: %s" %(self.port))
            
            while True:
                client, addr = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(client, addr))
                thread.start()
                
    def handle_client(self, client):
        with client:
            writer = client.makeFile('w')
            reader = client.makeFile('r')
            handle = None
            try:
                writer.write("Connection to the File Exchange System is successful!")
                writer.flush()
                
                while True:
                    client_input = reader.readLine().strip()
                    if not client_input:
                        break
                    
                    commands = client_input.split(" ")
                    instruc = commands[0]
                    
                    if not handle and (instruc != '/register'):
                        writer.write("Register a handle/alias first!\n")
                    elif instruc == '/register' and handle:
                        client_handle = self.register(commands, writer)
                    else:
                        # Client attempting to join again
                        if instruc == "/join":
                            writer.write("Already joined the server!\n")
                        # Client wants to disconnect
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
                            self.handle_store(commands, writer, reader, handle)
                        elif instruc == "/dir":
                            writer.write("OK\n")
                            writer.flush()
                            self.dir_files(writer)
                        elif instruc == "/?":
                            self.ask_help(writer)
                        else:
                            writer.write("Error: Unknown command.\n")
            finally:
                if handle:
                    self.clients.pop(handle.lower(), None)
                client.close()
                
    def register(self ,commands, writer):
        if len(commands) == 2:
            handle = commands[1]
            if handle.lower() not in self.clients:
                self.clients[(handle.lower())] = writer
                writer.write("Handle registered: %s\n" %(handle))
                print("Handle registered: %s\n" %(handle))
                return handle
            else:
                writer.write("Error: Handle already in use.\n")
        else:
            writer.write("Error: Invalid command for syntax /register.\n")
        return None
    
    def create_dir(self):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
            print("Directory successfully created: %s" %(self.dir_path))
            
    def dir_files(self, writer):
        files = os.listdir(self.dir_path)
        file_list = "\n".join(files)
        writer.write(f"<SOM>\n{file_list}\n<EOM>\n")
            
    def disconnect(self, writer, handle):
        if handle:
            self.clients.pop(handle.lower(), None)
        writer.write("Disconnected from the server.\n")
        writer.flush()
        
    def handle_store(self, commands, writer, reader, handle):
        if len(commands) < 2:
            writer.write("Error: Filename missing\n")
            return

        filename = commands[1]
        path = os.path.join(self.directory_path, filename)
        try:
            file_length = int(reader.readline().strip())
        except ValueError:
            writer.write("Error: Invalid File Length\n")
            return

        try:
            with open(path, 'wb') as file:
                total_read = 0
                while total_read < file_length:
                    data = reader.read(4096)
                    if not data:
                        break
                    file.write(data.encode())
                    total_read += len(data)
            print(f"Received {filename} From {handle}")
            writer.write(f"File {filename} received successfully.\n")
        except Exception as e:
            writer.write(f"Error storing file: {e}\n")
        
    def get_file(self, commands, client, writer, handle):
        if len(commands) < 2:
            writer.write("Error: Enter a filename.\n")
            return
        
        filename = commands[1]
        path = os.path.join(self.dir_path, filename)
        
        if not os.path.isfile(path):
            writer.write("Error: File does not exist.\n")
            return
        
        file_size = os.path.isfile(path)
        writer.write("File size: %s\n" %file_size)
        writer.flush()
        
        # Delay the sending of file
        time.sleep(3)
        
        try: 
            with open(path, 'rb') as file:
                client.send_file(f)
            print(f"File {filename} sent to {self.clients[handle]}")
        except Exception as e:
            writer.write(f"Error sending file: {e}\n")
            
    
    def ask_help(self, writer):
        response = (
            "<SOM>Available commands: \n"
            "/join <server_ip> <port> - Connect to the server\n"
            "/leave - Disconnect from the server\n"
            "/register <handle> - Register a unique handle\n"
            "/store <filename> - Send file to server\n"
            "/dir - List files on server\n"
            "/get <filename> - Fetch file from server\n"
            "/? - Show this help message<EOM>\n"
        )
        writer.write(response)
    
# If this file is running, make it main and start the server.        
if __name__ == "__main__":
    server = Server()