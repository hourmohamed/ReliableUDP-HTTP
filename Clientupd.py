from udp import ReliableUDP

client = ReliableUDP()
client.bind(('127.0.0.1', 0))  # Let OS pick free port
server_addr = ('127.0.0.1', 8080)

# Send GET request and wait for response
request = (
    "GET / HTTP/1.0\r\n"
    "Host: 127.0.0.1\r\n"
    "User-Agent: ReliableClient\r\n\r\n"
)
print("Sending GET request...")
client.reliable_send(server_addr, request.encode())
response, _ = client.reliable_recv()
print("[Response]\n", response.decode())

# Send POST request and wait for response
request = (
    "POST /submit HTTP/1.0\r\n"
    "Host: 127.0.0.1\r\n"
    "Content-Length: 13\r\n"
    "Content-Type: text/plain\r\n\r\n"
    "Hello, Server!"
)
print("Sending POST request...")
client.reliable_send(server_addr, request.encode())
response, _ = client.reliable_recv()
print("[Response]\n", response.decode())
