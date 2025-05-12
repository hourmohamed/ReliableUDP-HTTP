import socket
import time
import threading
import random
import struct
import hashlib


SYN = 0x01
ACK = 0x02
FIN = 0x04


class ReliableUDP:
    def __init__(self, loss_prob=0.1, corrupt_prob=0.1, timeout=2.0):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seq = 0
        self.loss_prob = loss_prob
        self.corrupt_prob = corrupt_prob
        self.timeout = timeout

    def bind(self,address):
        self.server.bind(address)
    
    def checksum(self, msg):
        return hashlib.md5(msg).digest
    
    def make_packet(self, flags, seq, payload=b''):
        # 2 bytes header: 1 byte for flag, 1 byte for seqNum
        header = struct.pack('!B I', flags, seq)
        body = header + payload
        cs = self.checksum(body)
        return cs + body

    def parse_packet(self, packet):
        # cs_recv-> checksum
        # rest->payload and header
        cs_recv, rest = packet[:16], packet[16:]

        if self.checksum(rest) != cs_recv:
            return None  # Corrupt
        
        flags, seq = struct.unpack('!B I', rest[:5])
        payload = rest[5:]
        return flags, seq, payload
    
    
    
    
    
        