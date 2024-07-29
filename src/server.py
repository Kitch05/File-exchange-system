import threading
import time
import socket
from datetime import datetime
import os

class Server :
    def __init__(self):
        self.host = 'localhost'
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
                    
                    # Client attempting to join again
                    if instruc == "/join":
                        writer.write("Already joined the server!\n")
                    # Client wants to disconnect
                    elif instruc == "/leave":
                        # self.handle_leave(writer, handle)
                        break
            finally:
                if handle:
                    self.clients.pop(handle.lower(), None)
                client.close()
                
            
    def create_dir(self):
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
            print("Directory successfully created: %s" %(self.dir_path))
    
# If this file is running, make it main and start the server.        
if __name__ == "__main__":
    server = Server()