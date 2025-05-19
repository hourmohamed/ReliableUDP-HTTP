# udp.py
import socket
import random
import time
from packet import Packet

TIMEOUT = 8

class TCP:
    def __init__(self, is_server=False, ip='127.0.0.1', port=12345):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(TIMEOUT)

        self.ip = ip
        self.addr = (ip, port)
        self.is_server = is_server
        self.seq = random.randint(1000, 5000)
        self.peer_addr = None
        self.ack_num = 0
        self.corruption_rate = 0.0

        if is_server:
            self.socket.bind(self.addr)
            print(f"[Server] Listening on {self.addr}")
        else:
            self.socket.bind(('0.0.0.0', 0))  # Client binds to ephemeral port
            print(f"[Client] ready to connect to {self.addr}")

    def set_corruption_rate(self, rate):
        """Set probability of simulated packet corruption (0.0 to 1.0)"""
        self.corruption_rate = rate

    def hand_shake(self):
        return self._server_handshake() if self.is_server else self._client_handshake()

    def _server_handshake(self):
        print("[Server] Waiting for SYN ..")
        try:
            data, addr = self.socket.recvfrom(1024)
            pkt = Packet.from_json(data.decode())
            if pkt.flags.get("SYN"):
                print(f"[Server] SYN received from {addr}")
                self.peer_addr = addr

                syn_ack = Packet(
                    seq_num=self.seq,
                    ack_num=pkt.seq_num + 1,
                    flags={"SYN": True, "ACK": True, "FIN": False}
                )
                self.socket.sendto(syn_ack.to_json().encode(), addr)

                data, _ = self.socket.recvfrom(1024)
                ack = Packet.from_json(data.decode())
                if ack.flags.get("ACK"):
                    print("[Server] Handshake complete")
                    return True
        except socket.timeout:
            print("[Server] Timeout waiting for handshake.")
        return False

    def _client_handshake(self):
        syn = Packet(seq_num=self.seq, ack_num=0, flags={"SYN": True, "ACK": False, "FIN": False})
        self.socket.sendto(syn.to_json().encode(), self.addr)

        try:
            data, addr = self.socket.recvfrom(1024)
            pkt = Packet.from_json(data.decode())
            if pkt.flags.get("SYN") and pkt.flags.get("ACK"):
                print("[Client] received SYN-ACK")
                self.peer_addr = addr

                ack = Packet(seq_num=pkt.ack_num, ack_num=pkt.seq_num + 1, flags={"SYN": False, "ACK": True, "FIN": False})
                self.socket.sendto(ack.to_json().encode(), addr)
                print("[Client] Handshake complete")
                return True
        except socket.timeout:
            print("[Client] Timeout waiting for SYN-ACK.")
        return False
    

    # def send(self, data: bytes):
    #     packet = Packet(
    #         seq_num=self.seq,
            
    #         ack_num=0,
    #         flags={"SYN": False, "ACK": False, "FIN": False},
    #         payload=data
    #     )

    #     ack_received = False
    #     while not ack_received:
    #         print(f"[Send] Sending packet seq={packet.seq_num}")
    #         self.socket.sendto(packet.to_json().encode(), self.peer_addr)

    #         try:
    #             self.socket.settimeout(1)
    #             ack_data, _ = self.socket.recvfrom(1024)
    #             ack_pkt = Packet.from_json(ack_data.decode())
    #             if ack_pkt.flags.get("ACK") and ack_pkt.ack_num == packet.seq_num + 1:
    #                 print(f"[Send] ACK received for seq={packet.seq_num}")
    #                 self.seq += 1
    #                 ack_received = True
    #         except socket.timeout:
    #             print("[Send] Timeout waiting for ACK, retransmitting..")




    def send(self, data, max_retries=15):
        """Send data with checksum and retransmission on failure"""
        original_packet = Packet(
            seq_num=self.seq,
            ack_num=self.ack_num,
            flags={"DATA": True},
            payload=data
        )
        
       

        for attempt in range(max_retries):

            packet_bytes = original_packet.to_bytes()
             # Randomly simulate corruption based on corruption_rate
            if random.random() < self.corruption_rate:
                packet_bytes = Packet.corrupt_bytes(packet_bytes)
            try:
                self.socket.sendto(packet_bytes, self.peer_addr)
                print(f"[Send] Sent packet (seq={original_packet.seq_num}), attempt {attempt+1}")

                # Wait for ACK
                ack_data, _ = self.socket.recvfrom(1024)
                ack_packet = Packet.from_bytes(ack_data)
                
                if ack_packet.flags["ACK"] and ack_packet.ack_num == original_packet.seq_num + 1:
                    self.seq += 1
                    return True

            except (socket.timeout, ValueError) as e:
                print(f"[Send] Error: {str(e)}, retrying...")
                # time.sleep(0.2)
                continue

        print("[Send] Max retries reached, giving up")
        return False



    # def recv(self) -> bytes:
    #     try:
    #         data, addr = self.socket.recvfrom(1024)
    #         pkt = Packet.from_json(data.decode())
    #         print(f"[Recv] Received packet seq={pkt.seq_num}")

    #         # Send ACK
    #         ack = Packet(
    #             seq_num=self.seq,
    #             ack_num=pkt.seq_num + 1,
    #             flags={"SYN": False, "ACK": True, "FIN": False}
    #         )
    #         self.socket.sendto(ack.to_json().encode(), addr)
    #         print(f"[Recv] Sent ACK for seq={pkt.seq_num}")

    #         return pkt.payload
    #     except socket.timeout:
    #         print("[Recv] Timeout, no data received.")
    #         return b''



    def recv(self):
        """Receive data with checksum verification"""
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                try:
                    packet = Packet.from_bytes(data)
                    print(f"[Recv] Received valid packet (seq={packet.seq_num})")

                    # Send ACK
                    ack = Packet(
                        seq_num=self.seq,
                        ack_num=packet.seq_num + 1,
                        flags={"ACK": True, }
                    )
                    self.socket.sendto(ack.to_bytes(), addr)
                    
                    self.ack_num = packet.seq_num + 1
                    return packet.payload

                except ValueError as e:
                    print(f"[Recv] Dropped corrupted packet: {str(e)}")
                    continue
            except socket.timeout:
                print("[Recv] Timeout waiting for packet")
                return None
            except ConnectionResetError:
                print("[Recv] Connection reset by peer")
                return None
        


    def close(self):
        print("[Connection] Closing socket.")
        self.socket.close()
