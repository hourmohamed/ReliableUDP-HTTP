import socket
import time
import threading
import random
import struct

socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
socket.bind(('localhost', 9999))

while True:
    data, addr = socket.recvfrom(1024)
    