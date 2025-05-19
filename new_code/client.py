from udp import TCP
from packet import Packet
import time

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
    client.set_corruption_rate(0.8)
    if client.hand_shake():
        print("[Client] Connected successfully")
        
        num_pkts = 5
        while num_pkts:
            # Construct packet manually
            if num_pkts==1:
                payload = b"GET /index.html HTTP/1.0\r\n\r\n"
                packet = Packet(seq_num=1, ack_num=0, flags={"DATA": True, "FIN":True}, payload=payload)
            else:
                payload = b"GET /index.html HTTP/1.0\r\n\r\n"
                packet = Packet(seq_num=1, ack_num=0, flags={"DATA": True}, payload=payload)
                print(f"[Client] Sending packet with checksum: {packet.checksum}")
            if client.send(packet.to_json().encode()):
                print("[Client] Message successfully sent and acknowledged")
                num_pkts-=1
            else:
                print("[Client] Failed to send message after retries")
                break
           
                
            
        # time.sleep(1)

    client.close()


if __name__ == "__main__":
    main()
