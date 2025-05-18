from udp import TCP
from packet import Packet

# def main():
    # client = TCP(is_server=False, ip='127.0.0.1', port=12345)
    # if client.hand_shake():
    #     print("[Client] Connected successfully")

    #     # Send data
    #     message = b"GET /index.html HTTP/1.0 tas tas tas \r\n\r\n"
    #     client.send(message)

    # client.close()

        # from packet import Packet

def main():
    client = TCP(is_server=False, ip='127.0.0.1', port=12345)
    if client.hand_shake():
        print("[Client] Connected successfully")

        # Construct packet manually
        payload = b"GET /index.html HTTP/1.0\r\n\r\n"
        packet = Packet(seq_num=1, ack_num=0, flags={"DATA": True}, payload=payload)
        print(f"[Client] Sending packet with checksum: {packet.checksum}")
        client.send(packet.to_json().encode())  

    client.close()


if __name__ == "__main__":
    main()
