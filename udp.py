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
    def __init__(self, timeout=2.0):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seq = 0
        self.timeout = timeout

    def bind(self,address):
        self.server.bind(address)
    

    # error detection
    def checksum(self, data):
        cs = sum(data) % 256
        return struct.pack('!B', cs)  # 1 byte
    

    def make_packet(self, flags, seq, payload=b''):
        # Packet structure:
        # 1 byte checksum | 1 byte flags | 4 bytes sequence | payload

        header = struct.pack('!B I', flags, seq)
        body = header + payload
        cs = self.checksum(body)
        return cs + body



    
    def parse_packet(self, packet):
        
        if len(packet) < 6:  # 1 checksum + 1 flag + 4 seq
            return None
        
        # cs_recv-> checksum
        # rest->payload and header
        cs_recv, rest = packet[:1], packet[1:]
        if self.checksum(rest) != cs_recv:
            return None
        
        flags, seq = struct.unpack('!B I', rest[:5])
        payload = rest[5:]
        return flags, seq, payload
    
    
    
    
    
        