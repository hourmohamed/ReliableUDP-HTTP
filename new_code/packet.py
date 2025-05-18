# packet.py
import json
import zlib
import struct
import base64
import random

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
        self.payload = payload if isinstance(payload, bytes) else payload.encode()
        self.checksum = self.compute_checksum()
        self.corrupted = False

    # def compute_checksum(self):
    #     content = f"{self.seq_num}{self.ack_num}{self.flags}{self.payload}"
    #     return zlib.crc32(content.encode())

    # def compute_checksum(self):
    #     """Calculate checksum including all critical fields"""
    #     header = struct.pack(HEADER_FORMAT, self.seq_num, self.ack_num, 
    #                        self.flags_to_byte(), len(self.payload))
    #     return zlib.crc32(header + self.payload)

    def compute_checksum(self):
        """Calculate checksum including all critical fields"""
        flags_byte = 0
        if self.flags.get("SYN"): flags_byte |= 0b00000001
        if self.flags.get("ACK"): flags_byte |= 0b00000010
        if self.flags.get("FIN"): flags_byte |= 0b00000100
        if self.flags.get("DATA"): flags_byte |= 0b00001000
        
        header = struct.pack(HEADER_FORMAT, 
                           self.seq_num, 
                           self.ack_num, 
                           flags_byte, 
                           len(self.payload))
        return zlib.crc32(header + self.payload)
    
    def flags_to_byte(self):
        """Convert flags dict to single byte"""
        byte = 0
        if self.flags.get("SYN"): byte |= 0b00000001
        if self.flags.get("ACK"): byte |= 0b00000010
        if self.flags.get("FIN"): byte |= 0b00000100
        if self.flags.get("DATA"): byte |= 0b00001000
        return byte



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

    
    # def to_bytes(self):
    #     header=struct.pack(HEADER_FORMAT,self.seq_num,self.ack_num,self.flags,len(self.payload))
    #     return header+self.payload


    def to_bytes(self):
        """Serialize packet with checksum"""
        if self.corrupted:
            bad_checksum = random.randint(0, 0xFFFFFFFF)
            header = struct.pack(HEADER_FORMAT, self.seq_num, self.ack_num,
                               self.flags_to_byte(), len(self.payload))
            return header + struct.pack("!I", bad_checksum) + self.payload
        
        header = struct.pack(HEADER_FORMAT, self.seq_num, self.ack_num,
                           self.flags_to_byte(), len(self.payload))
        return header + struct.pack("!I", self.checksum) + self.payload
    
    # @classmethod
    # def from_bytes(cls,data):
    #     header=data[:HEADER_SIZE]
    #     seq,ack,flags,length=struct.unpack(HEADER_FORMAT,header)
    #     payload=data[HEADER_SIZE:HEADER_SIZE+length]
    #     return cls(seq,ack,flags,payload)


    @classmethod
    def from_bytes(cls, data):
        """Deserialize packet and verify checksum"""
        header = data[:HEADER_SIZE]
        seq, ack, flags_byte, length = struct.unpack(HEADER_FORMAT, header)
        
        flags = {
            "SYN": bool(flags_byte & 0b00000001),
            "ACK": bool(flags_byte & 0b00000010),
            "FIN": bool(flags_byte & 0b00000100),
            "DATA": bool(flags_byte & 0b00001000)
        }
        
        checksum = struct.unpack("!I", data[HEADER_SIZE:HEADER_SIZE+4])[0]
        payload = data[HEADER_SIZE+4:HEADER_SIZE+4+length]
        
        # Create temporary packet for verification
        temp_pkt = cls(seq, ack, flags, payload)
        if temp_pkt.checksum != checksum:
            raise ValueError("Checksum verification failed")
        
        return temp_pkt
    

    def simulate_corruption(self):
        """Toggle corruption simulation"""
        self.corrupted = not self.corrupted
        return self