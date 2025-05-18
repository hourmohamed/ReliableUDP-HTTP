from udp import TCP

def main():
    server = TCP(is_server=True, ip='127.0.0.1', port=12345)
    if server.hand_shake():
        print("[Server] Connection established")

        # Receive data
        data = server.recv()
        print(f"[Server] Received data:\n{data.decode()}")

    server.close()

if __name__ == "__main__":
    main()
