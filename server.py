import socket
import threading
import ssl

class Server:
    def __init__(self, host='192.168.1.75', port=50000):
        self.clients = {}
        self.client_ids = set()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(5)

        #context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        #context.load_cert_chain(certfile="path/to/certificate.pem", keyfile="path/to/key.pem")
        #self.sock = context.wrap_socket(self.sock, server_side=True)

        print(f"Server active on host:port {host}:{port}")

    def send_to_clients(self, message, sender_id, receiver_ids):
        for receiver_id in receiver_ids:
            if receiver_id in self.clients:
                try:
                    self.clients[receiver_id].send(f"From {sender_id}: {message}".encode('ascii'))
                except:
                    self.remove_client(receiver_id)

    def broadcast(self, message, sender_id):
        # Formatted_message provides a format for providing the sender_id in group chat for clarity or who is who
        formatted_message = f"{sender_id}: {message}"
        for client_id, client in self.clients.items():
            if client_id != sender_id:
                try:
                    client.send(formatted_message.encode('ascii'))
                except:
                    client.close()
                    self.remove_client(client_id)

    def list_clients(self, requestor_id):
        client_list = "\n".join([cid for cid in self.client_ids if cid != requestor_id])
        if client_list:
            message = f"Connected Clients:\n{client_list}"
        else:
            message = "No other clients connected."
        self.clients[requestor_id].send(message.encode('ascii'))

    def handle_client(self, client, client_id):
        # Set to track clients who are in group chat mode
        group_chat_clients = set() 
        

        while True:
            try:
                message = client.recv(1024).decode('ascii')
                if message.startswith("/list"):
                    self.list_clients(client_id)
                elif message.startswith("/send"):
                    # When not in group chat, we act as a private messenger chat program (much like /tell or /whisper or /message in games)
                    _, receiver_ids, msg = message.split(" ", 2)
                    self.send_to_clients(msg, client_id, receiver_ids.split(","))
                elif message.startswith("/broadcast"):
                    msg = message.split(" ", 1)[1]
                    self.broadcast(msg, client_id)
                    # Group chat mode allows for 'server broadcast' of messages within the chat, rather than needing to do a /send c1,c2,c3 <message>.
                    # Note /send still works, it's just groupchat mode better gives the illusion/feeling of a group chat than just having the server send all non-'/' tagged messages as broadcasts
                elif message == "/groupchat":
                    if client_id in group_chat_clients:
                        group_chat_clients.remove(client_id)
                    else:
                        group_chat_clients.add(client_id)
                elif client_id in group_chat_clients:
                    # Broadcast all messages from clients if in group chat mode. Makes the chat feel more like natural group chat expectations.
                    self.broadcast(message, client_id)
                else:
                    pass
            except:
                self.remove_client(client_id)
                break

    def remove_client(self, client_id):
        if client_id in self.clients:
            del self.clients[client_id]
            self.client_ids.remove(client_id)
            print(f"{client_id} Disconnected")

    def run(self):
        while True:
            client, address = self.sock.accept()
            client_id = f"{address[0]}:{address[1]}"
            self.client_ids.add(client_id)
            self.clients[client_id] = client
            print(f"{client_id} Connected")
            welcome_message = f"You are connected with ID: {client_id}."
            client.send(welcome_message.encode('ascii'))
            self.list_clients(client_id)
            threading.Thread(target=self.handle_client, args=(client, client_id)).start()

if __name__ == "__main__":
    server = Server()
    server.run()