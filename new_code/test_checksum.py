from packet import Packet

# Test cases for checksum functionality
def test_checksum():
    # Test with identical packets
    pkt1 = Packet(seq_num=100, ack_num=200, flags={"SYN": True}, payload=b"test")
    pkt2 = Packet(seq_num=100, ack_num=200, flags={"SYN": True}, payload=b"test")
    assert pkt1.checksum == pkt2.checksum, "Identical packets should have same checksum"
    
    # Test with different payloads
    pkt3 = Packet(seq_num=100, ack_num=200, flags={"SYN": True}, payload=b"different")
    assert pkt1.checksum != pkt3.checksum, "Different payloads should have different checksums"
    
    # Test with corrupted data
    corrupted_json = pkt1.to_json().replace('"seq_num":100', '"seq_num":101')
    try:
        Packet.from_json(corrupted_json)
        assert False, "Checksum verification should have failed"
    except ValueError:
        pass
    
    print("All checksum tests passed!")

test_checksum()