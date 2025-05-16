import socket
import time
import threading
import random
import struct


SYN = 0x01
ACK = 0x02
FIN = 0x04
DATA = 0x08

WINDOW_SIZE = 5
MAX_SEQ = 256
TIMEOUT = 2

class ReliableUDP:
    def __init__(self, timeout=2.0, loss_rate=0.1):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seq = 0
        self.ack = 0
        self.timeout_val = timeout
        self.loss_rate = loss_rate
        self.expected_seq = 0
        self.buffer = {}  # Buffer for out-of-order packets
        self.server.settimeout(None)

    def bind(self, address):
        self.server.bind(address)

    def checksum(self, data):
        cs = sum(data) % 256
        return struct.pack('!B', cs)

    def unreliable_sendto(self, packet, addr):
        rand = random.random()
        if rand < self.loss_rate:
            print("[DROP] Simulated packet loss")
            return
        if rand < self.loss_rate * 2:
            print("[DUP] Simulated packet duplication")
            self.server.sendto(packet, addr)
        self.server.sendto(packet, addr)

    def reliable_send(self, adr, payload):
        pkt = self.make_packet(DATA, self.seq, payload)
        while True:
            self.unreliable_sendto(pkt, adr)
            try:
                self.server.settimeout(self.timeout_val)
                response, _ = self.server.recvfrom(1024)
                parsed_pkt = self.parse_packet(response)
                if parsed_pkt:
                    flags, ack_seq, _ = parsed_pkt
                    if (flags & ACK) and ack_seq == self.seq:
                        self.seq = (self.seq + 1) % MAX_SEQ
                        break
            except socket.timeout:
                print("timeout, waiting for retransmission")

    def reliable_recv(self):
        full_data = b''
        sender_addr = None
        while True:
            pkt, adr = self.server.recvfrom(1024)
            parsed_pkt = self.parse_packet(pkt)
            if not parsed_pkt:
                continue
            flags, seq, payload = parsed_pkt

            if flags & DATA:
                if sender_addr is None:
                    sender_addr = adr

                # Within window
                window_end = (self.expected_seq + WINDOW_SIZE) % MAX_SEQ
                in_window = (self.expected_seq <= seq < window_end) if self.expected_seq < window_end else (seq >= self.expected_seq or seq < window_end)

                if in_window:
                    if seq not in self.buffer:
                        print(f"[RECV] Received seq={seq}")
                        self.buffer[seq] = payload

                    # Always ACK what we received
                    ack_pkt = self.make_packet(ACK, seq)
                    self.server.sendto(ack_pkt, adr)

                    # Slide window and return data in order
                    while self.expected_seq in self.buffer:
                        full_data += self.buffer.pop(self.expected_seq)
                        self.expected_seq = (self.expected_seq + 1) % MAX_SEQ

                    if full_data:
                        return full_data, sender_addr

                else:
                    # Packet outside window: send ACK anyway
                    print(f"[OUT-OF-WINDOW] seq={seq}")
                    ack_pkt = self.make_packet(ACK, seq)
                    self.server.sendto(ack_pkt, adr)

    def make_packet(self, flags, seq, payload=b''):
        header = struct.pack('!B H', flags, seq)
        body = header + payload
        cs = self.checksum(body)
        return cs + body

    def parse_packet(self, packet):
        if len(packet) < 4:
            return None
        cs_recv, rest = packet[:1], packet[1:]
        if self.checksum(rest) != cs_recv:
            return None
        flags, seq = struct.unpack('!B H', rest[:3])
        payload = rest[3:]
        return flags, seq, payload
