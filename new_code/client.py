from udp import TCP

def main():
    client = TCP(is_server=False, ip='127.0.0.1', port=12345)
    if client.hand_shake():
        print("[Client] Connected successfully")

        # Send data
        message = b"GET /index.html HTTP/1.0 tas tas tas \r\n\r\n"
        client.send(message)

    client.close()

if __name__ == "__main__":
    main()
