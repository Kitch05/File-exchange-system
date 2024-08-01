import socket
import os

class Client:
    def __init__(self):
        self.socket = None

    def connect(self, address, port):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((address, port))
            print("Connected to the server.")
            self.reader = self.socket.makefile('r')
            self.writer = self.socket.makefile('w')
            print(self.reader.readline().strip())
            self.start()
        except Exception as e:
            print(f"Error: Connection to the Server has failed! Please check IP Address and Port Number. Details: {e}")

    def start(self):
        try:
            print("Enter commands (Type /? for help):")

            while True:
                from_user = input()
                if from_user:
                    self.process_command(from_user)
                else:
                    break  # Exit if user input is empty (EOF, Ctrl+D)

        except Exception as e:
            print(f"An I/O error occurred: {e}")
        finally:
            self.close_resources()

    def process_command(self, from_user):
        try:
            tokens = from_user.split()
            command = tokens[0]

            if command == "/join":
                if len(tokens) == 3:
                    address = tokens[1]
                    port = int(tokens[2])
                    self.connect(address, port)
                else:
                    print("Error: Command parameters do not match or are not allowed. Usage: /join <server_ip> <port>")

            elif command == "/leave":
                if self.socket and len(tokens) == 1:
                    self.writer.write(command + "\n")
                    self.writer.flush()
                    self.handle_leave()
                else:
                    print("Error: Disconnection failed. Please connect to the server first.")

            elif command == "/register":
                if len(tokens) == 2:
                    self.writer.write(from_user + "\n")
                    self.writer.flush()
                    response = self.reader.readline().strip()
                    if "Error" in response:
                        print(response)
                    else:
                        print(response)
                else:
                    print("Error: Command parameters do not match or are not allowed. Usage: /register <username>")

            elif command == "/store":
                if len(tokens) == 2:
                    self.handle_store(tokens[1])
                else:
                    print("Error: Command parameters do not match or are not allowed. Usage: /store <filename>")

            elif command == "/dir":
                self.writer.write(command + "\n")
                self.writer.flush()
                response = self.reader.readline().strip()
                if response != "OK":
                    print(response)
                else:
                    self.display_server_message()

            elif command == "/get":
                if len(tokens) == 2:
                    self.handle_get(tokens[1])
                else:
                    print("Error: Command parameters do not match or are not allowed. Usage: /get <filename>")

            elif command == "/?":
                self.display_help()

            else:
                print("Error: Command not found.")
        except Exception as e:
            print(f"Server is Closed! {e}")
            self.handle_leave()

    def display_help(self):
        response = (
            "Available commands: \n"
            "/join <server_ip> <port> - Connect to the server\n"
            "/leave - Disconnect from the server\n"
            "/register <handle> - Register a unique handle\n"
            "/store <filename> - Send file to server\n"
            "/dir - List files on server\n"
            "/get <filename> - Fetch file from server\n"
            "/? - Show this help message\n"
        )
        print(response)

    def display_server_message(self):
        try:
            message_builder = []
            while True:
                line = self.reader.readline().strip()
                if line == "<SOM>":
                    continue  # Start of message, do nothing
                elif line == "<EOM>":
                    break  # End of message, exit loop
                else:
                    message_builder.append(line)
            message = "\n".join(message_builder)
            print(message)
        except Exception as e:
            print(f"Error displaying server message: {e}")

    def handle_leave(self):
        print("Disconnecting from server...")
        self.close_resources()

    def handle_store(self, filename):
        try:
            if not os.path.isfile(filename):
                print("Error: File not found.")
                return

            self.writer.write(f"/store {filename}\n")
            self.writer.flush()
            response = self.reader.readline().strip()
            if response != "OK":
                print(response)
                return

            file_size = os.path.getsize(filename)
            self.writer.write(f"{file_size}\n")
            self.writer.flush()

            with open(filename, "rb") as file:
                while chunk := file.read(4096):
                    self.socket.sendall(chunk)
            print(f"File {filename} sent to server.")
            print(self.reader.readline().strip())
        except Exception as e:
            print(f"Failed Sending: {e}")
        finally:
            print("Enter commands (Type /? for help):")

    def handle_get(self, filename):
        try:
            self.writer.write(f"/get {filename}\n")
            self.writer.flush()
            response = self.reader.readline().strip()
            if response != "OK":
                print(response)
                return

            file_length = int(self.reader.readline().strip())
            with open(filename, "wb") as file:
                total_read = 0
                while total_read < file_length:
                    data = self.socket.recv(4096)
                    if not data:
                        break
                    file.write(data)
                    total_read += len(data)
            print(f"Received {filename} from the server")
        except Exception as e:
            print(f"Error storing file: {e}")

    def close_resources(self):
        try:
            if self.socket:
                self.socket.close()
        except Exception as e:
            print(f"Error closing resources: {e}")
        finally:
            self.socket = None

if __name__ == "__main__":
    client = Client()
    while True:
        command = input("Enter command (use /join <IP> <port> to connect): ")
        client.process_command(command)
