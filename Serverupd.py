from udp import ReliableUDP

server = ReliableUDP()
server.bind(('127.0.0.1', 8080))
print("Server ready...")


while True:
    request_data, addr = server.reliable_recv()
    request = request_data.decode()
    print("[Request]\n", request)

    lines = request.splitlines()
    if not lines:
        continue

    method, path, _ = lines[0].split()

    if method == "GET":
        if path == "/":
            body = "<h1>Welcome to ReliableUDP HTTP Server</h1>"
            response = (
                "HTTP/1.0 200 OK\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Content-Type: text/html\r\n\r\n"
                + body
            )
        else:
            response = "HTTP/1.0 404 Not Found\r\nContent-Length: 0\r\n\r\n"

        server.reliable_send(addr, response.encode())

    elif method == "POST":
        content = request.split("\r\n\r\n", 1)[-1]
        print("Received POST data:", content)
        body = "Data received"
        response = (
            "HTTP/1.0 200 OK\r\n"
            f"Content-Length: {len(body)}\r\n"
            "Content-Type: text/plain\r\n\r\n"
            + body
        )
        server.reliable_send(addr, response.encode())

    else:
        response = "HTTP/1.0 404 Not Found\r\nContent-Length: 0\r\n\r\n"
        server.reliable_send(addr, response.encode())
