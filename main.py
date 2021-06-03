from ProxyServer import ProxyServer

DEFAULT_IP = "0.0.0.0"
DEFAULT_PORT = 5000


def main():
    host_addr = input("Type ip address (or type '-' for default value (0.0.0.0)): ")
    port = input("Type port (or type '-' for default value (5000)): ")

    try:
        if port != '-':
            port = int(port)
        else:
            port = DEFAULT_PORT
    except ValueError:
        print("Port value must be a number")
        exit(1)

    if host_addr == '-':
        host_addr = DEFAULT_IP

    proxy_server = ProxyServer()
    proxy_server.run_server(host_addr, port)


if __name__ == '__main__':
    main()
