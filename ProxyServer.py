import socket
from threading import Thread
from RequestParser import RequestParser

CONNECTION_RESPONSE = "HTTP/1.0 200 Connection established\r\n\r\n"


class ProxyServer:
    def __init__(self):
        self.listening_socket = None
        self.buf_length = 8192

    def run_server(self, ip="0.0.0.0", port=5000):
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.listening_socket.bind((ip, port))
        except socket.error:
            print("Unable to bind socket on {}:{}".format(ip, port))
            self.listening_socket.close()
            exit(2)

        self.listening_socket.listen(20)
        print(f"Listening on {ip}:{port}")

        while True:
            client, addr = self.listening_socket.accept()
            print(f"Accept connection from {addr[0]}:{addr[1]}")
            Thread(target=self.handle_request, args=(client,)).start()

    def handle_request(self, client):
        data_from_client = client.recv(self.buf_length)
        request = RequestParser.parse_request(data_from_client)

        self.send_to_server(request, client)

    def send_to_server(self, request, client):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            server_socket.connect((request["host"], request["port"]))
        except socket.error:
            print(f'Could not connect to {request["host"]}:{request["port"]}')
            client.close()
            server_socket.close()
            return

        if "CONNECT" in request["meta"]:
            self.run_https_messaging(request, client, server_socket)
        else:
            self.run_http_handle(request, client, server_socket)

    def run_http_handle(self, request, client, server_socket):
        server_socket.sendall(request["orig_data"])

        while True:
            response = server_socket.recv(self.buf_length)

            if not response:
                break

            client.sendall(response)

        server_socket.close()
        client.close()

    def run_https_messaging(self, request, client, server_socket):
        client.sendall(CONNECTION_RESPONSE.encode())

        client.setblocking(False)
        server_socket.setblocking(False)

        # Forwarding messages from client to server and vice-versa
        while True:
            try:
                data = client.recv(self.buf_length)
                if not data:
                    print("Data from client is empty (In connection with {}:{})"
                          .format(request["host"], request["port"]))
                    break

                server_socket.sendall(data)
            except socket.error:
                pass

            try:
                response = server_socket.recv(self.buf_length)
                if not response:
                    print("Data from server is empty (Address: {}:{})"
                          .format(request["host"], request["port"]))
                    break
                client.sendall(response)
            except socket.error:
                pass

        server_socket.close()
        client.close()
