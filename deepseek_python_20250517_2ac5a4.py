import threading
import time
import unittest
from udp import ReliableUDP  # Assuming your code is in reliable_udp.py

class TestReliableUDP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Common parameters
        cls.server_addr = ('127.0.0.1', 5000)
        cls.client_addr = ('127.0.0.1', 5001)
        cls.loss_rate = 0.3  # Simulate 30% packet loss for testing reliability
        cls.test_data = b"Hello, this is a test message for reliable UDP implementation!"

    def setUp(self):
        # Setup fresh instances for each test
        self.server = ReliableUDP(loss_rate=self.loss_rate)
        self.client = ReliableUDP(loss_rate=self.loss_rate)
        self.server.bind(self.server_addr)

    def tearDown(self):
        self.server.close()
        self.client.close()

    def test_connection_handshake(self):
        """Test the 3-way handshake connection establishment"""
        def server_accept():
            self.server.accept()

        # Start server in a separate thread
        server_thread = threading.Thread(target=server_accept)
        server_thread.start()

        # Client connects
        result = self.client.connect(self.server_addr)
        self.assertTrue(result)
        self.assertEqual(self.client.connection_state, 'ESTABLISHED')
        
        server_thread.join(timeout=1)
        self.assertEqual(self.server.connection_state, 'ESTABLISHED')

    def test_data_transfer_client_to_server(self):
        """Test reliable data transfer from client to server"""
        self.server.accept()  # Non-blocking accept for test
        self.client.connect(self.server_addr)

        # Send data from client
        self.client.send(self.test_data)

        # Receive on server
        received = self.server.recv()
        self.assertEqual(received, self.test_data)

    def test_data_transfer_server_to_client(self):
        """Test reliable data transfer from server to client"""
        self.server.accept()  # Non-blocking accept for test
        self.client.connect(self.server_addr)

        # Send data from server
        self.server.send(self.test_data)

        # Receive on client
        received = self.client.recv()
        self.assertEqual(received, self.test_data)

    def test_large_data_transfer(self):
        """Test transfer of data larger than the window size"""
        self.server.accept()
        self.client.connect(self.server_addr)

        # Create a large message (larger than default window size)
        large_data = b"X" * 1024 * 10  # 10KB

        # Send from client to server
        self.client.send(large_data)
        received = self.server.recv()
        self.assertEqual(len(received), len(large_data))
        self.assertEqual(received, large_data)

        # Send from server to client
        self.server.send(large_data)
        received = self.client.recv()
        self.assertEqual(len(received), len(large_data))
        self.assertEqual(received, large_data)

    def test_multiple_messages(self):
        """Test multiple sequential messages"""
        self.server.accept()
        self.client.connect(self.server_addr)

        messages = [b"Message 1", b"Message 2", b"Message 3"]
        
        for msg in messages:
            self.client.send(msg)
            received = self.server.recv()
            self.assertEqual(received, msg)

    def test_out_of_order_packets(self):
        """Test handling of out-of-order packets"""
        # Temporarily disable packet loss for this test
        self.server.loss_rate = 0
        self.client.loss_rate = 0
        
        self.server.accept()
        self.client.connect(self.server_addr)

        # Monkey patch the send method to reorder packets
        original_send = self.client.socket.sendto
        packets = []
        
        def reorder_send(packet, addr):
            packets.append(packet)
            if len(packets) >= 3:  # Wait for 3 packets then send in reverse order
                for p in reversed(packets):
                    original_send(p, addr)
                packets.clear()
        
        self.client.socket.sendto = reorder_send

        # Send data that will be split into multiple packets
        data = b"Start" + b"X" * 2000 + b"End"  # Should be split into multiple packets
        self.client.send(data)
        
        received = self.server.recv()
        self.assertEqual(received, data)

    def test_packet_loss_recovery(self):
        """Test recovery from simulated packet loss"""
        # Set high loss rate to ensure some packets are dropped
        self.server.loss_rate = 0.5
        self.client.loss_rate = 0.5
        
        self.server.accept()
        self.client.connect(self.server_addr)

        # Send data that will be split into multiple packets
        data = b"Start" + b"X" * 2000 + b"End"
        self.client.send(data)
        
        received = self.server.recv()
        self.assertEqual(received, data)

    def test_connection_teardown(self):
        """Test graceful connection termination"""
        self.server.accept()
        self.client.connect(self.server_addr)

        # Client initiates close
        self.client.close()
        
        # Verify states
        self.assertEqual(self.client.connection_state, 'CLOSED')
        
        # Server should eventually close
        timeout = time.time() + 5
        while self.server.connection_state != 'CLOSED' and time.time() < timeout:
            time.sleep(0.1)
        
        self.assertEqual(self.server.connection_state, 'CLOSED')

    def test_simultaneous_close(self):
        """Test simultaneous connection termination"""
        self.server.accept()
        self.client.connect(self.server_addr)

        # Both sides close simultaneously
        self.server.close()
        self.client.close()
        
        # Verify states
        self.assertEqual(self.server.connection_state, 'CLOSED')
        self.assertEqual(self.client.connection_state, 'CLOSED')

    def test_rapid_connect_disconnect(self):
        """Test rapid connection and disconnection"""
        for _ in range(5):  # Repeat multiple times
            self.setUp()  # Fresh instances
            
            self.server.accept()
            self.client.connect(self.server_addr)
            
            # Exchange some data
            self.client.send(b"ping")
            self.assertEqual(self.server.recv(), b"ping")
            
            self.server.send(b"pong")
            self.assertEqual(self.client.recv(), b"pong")
            
            self.client.close()
            self.server.close()

if __name__ == '__main__':
    unittest.main(verbosity=2)