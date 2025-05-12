import socket
import time
import threading
import random
import struct
import hashlib

# Flags
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
    
    
        