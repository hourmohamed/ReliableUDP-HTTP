# packet.py
import json
import zlib
import struct
import base64
HEADER_FORMAT = "!I I B H"  # Network order: unsigned int, unsigned int, unsigned char, unsigned short
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# Flag bits (you can combine flags using bitwise OR)
FLAG_SYN = 0b00000001
FLAG_ACK = 0b00000010
FLAG_FIN = 0b00000100
FLAG_DATA = 0b00001000
class Packet:
    def __init__(self, seq_num=0, ack_num=0, flags=None, payload=""):
        if flags is None:
            flags = {"SYN": False, "ACK": False, "FIN": False}
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.flags = flags
        self.payload = payload
        self.checksum = self.compute_checksum()

    def compute_checksum(self):
        content = f"{self.seq_num}{self.ack_num}{self.flags}{self.payload}"
        return zlib.crc32(content.encode())

    def to_json(self):
        return json.dumps({
            "seq_num": self.seq_num,
            "ack_num": self.ack_num,
            "flags": self.flags,
            "payload": base64.b64encode(self.payload).decode() if self.payload else "",
            "checksum": self.checksum  # <- Add this line
        })

    @staticmethod
    def from_json(data):
        import base64
        obj = json.loads(data)
        payload = base64.b64decode(obj["payload"]) if obj["payload"] else b""
        return Packet(
            seq_num=obj["seq_num"],
            ack_num=obj["ack_num"],
            flags=obj["flags"],
            payload=payload
        )

    
    def to_bytes(self):
        header=struct.pack(HEADER_FORMAT,self.seq_num,self.ack_num,self.flags,len(self.payload))
        return header+self.payload
    
    @classmethod
    def from_bytes(cls,data):
        header=data[:HEADER_SIZE]
        seq,ack,flags,length=struct.unpack(HEADER_FORMAT,header)
        payload=data[HEADER_SIZE:HEADER_SIZE+length]
        return cls(seq,ack,flags,payload)
