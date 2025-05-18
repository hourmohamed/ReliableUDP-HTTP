# udp.py
import socket
import random
from packet import Packet

TIMEOUT = 3

class TCP:
    def __init__(self, is_server=False, ip='127.0.0.1', port=12345):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(TIMEOUT)

        self.ip = ip
        self.addr = (ip, port)
        self.is_server = is_server
        self.seq = random.randint(1000, 5000)
        self.peer_addr = None

        if is_server:
            self.socket.bind(self.addr)
            print(f"[Server] Listening on {self.addr}")
        else:
            self.socket.bind(('0.0.0.0', 0))  # Client binds to ephemeral port
            print(f"[Client] ready to connect to {self.addr}")

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
    def send(self, data: bytes):
        packet = Packet(
            seq_num=self.seq,
            ack_num=0,
            flags={"SYN": False, "ACK": False, "FIN": False},
            payload=data
        )

        ack_received = False
        while not ack_received:
            print(f"[Send] Sending packet seq={packet.seq_num}")
            self.socket.sendto(packet.to_json().encode(), self.peer_addr)

            try:
                self.socket.settimeout(1)
                ack_data, _ = self.socket.recvfrom(1024)
                ack_pkt = Packet.from_json(ack_data.decode())
                if ack_pkt.flags.get("ACK") and ack_pkt.ack_num == packet.seq_num + 1:
                    print(f"[Send] ACK received for seq={packet.seq_num}")
                    self.seq += 1
                    ack_received = True
            except socket.timeout:
                print("[Send] Timeout waiting for ACK, retransmitting..")
    def recv(self) -> bytes:
        try:
            data, addr = self.socket.recvfrom(1024)
            pkt = Packet.from_json(data.decode())
            print(f"[Recv] Received packet seq={pkt.seq_num}")

            # Send ACK
            ack = Packet(
                seq_num=self.seq,
                ack_num=pkt.seq_num + 1,
                flags={"SYN": False, "ACK": True, "FIN": False}
            )
            self.socket.sendto(ack.to_json().encode(), addr)
            print(f"[Recv] Sent ACK for seq={pkt.seq_num}")

            return pkt.payload
        except socket.timeout:
            print("[Recv] Timeout, no data received.")
            return b''

    def close(self):
        print("[Connection] Closing socket.")
        self.socket.close()
