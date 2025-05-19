from udp import TCP

def main():
    server = TCP(is_server=True, ip='127.0.0.1', port=12345)
    if server.hand_shake():
        print("[Server] Connection established")
        while True:
            data = server.recv()
            if data is not None:
                try:
                    request = data.decode()
                    print(f"[Server] Received request:\n{request}")

                    # Basic HTTP parsing
                    if request.startswith("GET"):
                        resource = request.split()[1]
                        if resource == "/index.html":
                            response = b"HTTP/1.0 200 OK\r\n\r\n<html><body><h1>Welcome</h1></body></html>"
                        else:
                            response = b"HTTP/1.0 404 Not Found\r\n\r\n<html><body><h1>404 Not Found</h1></body></html>"

                    elif request.startswith("POST"):
                        response = b"HTTP/1.0 200 OK\r\n\r\n<html><body><h1>POST received</h1></body></html>"

                    else:
                        response = b"HTTP/1.0 400 Bad Request\r\n\r\n"

                    server.send(response)

                except UnicodeDecodeError:
                    print("[Server] Binary data received (cannot decode)")
            else:
                print("[Server] No valid data received")
                break



    server.close()

if __name__ == "__main__":
    main()
