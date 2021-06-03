import email
from io import StringIO
import socket
from threading import Thread

DEFAULT_IP = "0.0.0.0"
DEFAULT_PORT = 5000

CONNECTION_RESPONSE = "HTTP/1.0 200 Connection established\r\n\r\n"


class RequestParser:
    @staticmethod
    def parse_request(request_data):
        meta, headers = request_data.decode("utf-8").split('\r\n', 1)

        # construct a message from the request string
        message = email.message_from_file(StringIO(headers))

        # construct a dictionary containing the headers
        headers = dict(message.items())

        url = headers["Host"]
        if ':' in url:
            host, port = url.split(':')
        else:
            host, port = url, 80

        return {"orig_data": request_data, "meta": meta, "host": host, "port": int(port)}


class ProxyServer:
    def __init__(self):
        self.listening_socket = None
        self.buf_length = 8192

    def run_server(self, ip="0.0.0.0", port=5000):
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

        self.listening_socket.bind((ip, port))
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

            try:
                client.sendall(response)
            except Exception as e:
                print(f'Connection with client was destroyed')
                server_socket.close()
                client.close()
                return

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
            except socket.error as err:
                pass

            try:
                response = server_socket.recv(self.buf_length)
                if not response:
                    print("Data from server is empty (Address: {}:{})"
                          .format(request["host"], request["port"]))
                    break
                client.sendall(response)
            except socket.error as err:
                pass

        server_socket.close()
        client.close()


if __name__ == '__main__':
    host_addr = input("Put ip address (or put '-' for default values): ")
    port = input("Put port (or put '-' for default values): ")

    try:
        if port != '-':
            port = int(port)
        else:
            port = DEFAULT_PORT
    except:
        print("Port value should be number")
        exit(1)

    if host_addr == '-':
        host_addr = DEFAULT_IP

    proxy_server = ProxyServer()
    proxy_server.run_server(host_addr, port)
