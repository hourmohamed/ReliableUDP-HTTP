from udp import TCP

def main():
    server = TCP(is_server=True, ip='127.0.0.1', port=12345)
    if server.hand_shake():
        print("[Server] Connection established")

        # Receive data
        data = server.recv()
        if data is not None:
            try:
                print(f"[Server] Received data:\n{data.decode()}")
            except UnicodeDecodeError:
                print("[Server] Received binary data (cannot decode as text)")
        else:
            print("[Server] No valid data received")

    server.close()

if __name__ == "__main__":
    main()
