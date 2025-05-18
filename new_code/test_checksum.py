# test_checksum.py
from packet import Packet
import random

def test_checksum_verification():
    # Create a valid packet
    pkt = Packet(seq_num=100, ack_num=200, payload=b"test data")
    
    # Simulate corruption
    corrupted_data = pkt.to_bytes()[:-2] + bytes([random.randint(0, 255) for _ in range(2)])
    
    try:
        Packet.from_bytes(corrupted_data)
        print("TEST FAILED: Corrupted packet was accepted")
    except ValueError:
        print("TEST PASSED: Corrupted packet detected")

if __name__ == "__main__":
    test_checksum_verification()