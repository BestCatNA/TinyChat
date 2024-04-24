import socket
import threading
import sys
import logging
import ssl

# Setup logging
logging.basicConfig(filename='client.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

class Client:
    def __init__(self, host, port=50000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        try:
            self.sock.connect((host, port))
            logging.info(f"Connected to server at {host}:{port}")
            self.connected = True
        except socket.error as e:
            logging.error(f"Socket error: {e}. Unable to connect to the server.")

    def send_message(self):
        # This variable should make it so that users will not need to constantly retype who they are sending messages to
        last_command = None
        group_chat_mode = False
        while True:
            try:
                message = input("Enter message, /groupchat to toggle group chat mode, /list to see clients, or /send <id1,id2,...> <message> to message clients: ")
                if message == ".exit":
                    self.sock.sendall(message.encode('ascii'))
                    break
                elif message == "/groupchat":
                    group_chat_mode = not group_chat_mode
                    print("Group chat mode is now " + ("on" if group_chat_mode else "off"))
                    continue
                elif group_chat_mode:
                    message = "/broadcast " + message
                elif message.startswith("/"):
                    last_command = message
                else:
                    # If last_command is present, and the client sent a message this will use it behind the scenes for the user, no need to type ('sticky' chat)
                    if last_command and last_command.startswith("/send"):
                        _, receiver_ids = last_command.split(" ", 2)[:2]
                        message = f"/send {receiver_ids} {message}"

                self.sock.sendall(message.encode('ascii'))

            except Exception as e:
                logging.error(f"Error in send_message: {e}")
                break

    def receive_message(self):
        while True:
            try:
                message = self.sock.recv(1024).decode('ascii')
                if message:
                    print(message)  # Print received message to the console
                    logging.info(f"Received message: {message}")
                else:
                    logging.warning("Server closed the connection.")
                    break
            except Exception as e:
                logging.error(f"Error in receive_message: {e}")
                break

    def run(self):
        if self.connected:
            send_thread = threading.Thread(target=self.send_message)
            receive_thread = threading.Thread(target=self.receive_message)
            send_thread.start()
            receive_thread.start()

            send_thread.join()
            self.sock.close()
            receive_thread.join()
        else:
            logging.error("Client not connected. Exiting program.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error("Format: client.py <host> <port>")
    else:
        try:
            host = sys.argv[1]
            port = int(sys.argv[2])
            client = Client(host, port)
            client.run()
        except ValueError:
            logging.error("Invalid port number. Please enter an integer.")