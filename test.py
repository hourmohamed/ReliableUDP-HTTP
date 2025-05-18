import unittest
import threading
import time
import socket
import random
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TestReliableUDP')

# Import the ReliableUDP class
from udp import ReliableUDP

# Constants
HOST = '127.0.0.1'
PORT = 8088  # Changed to a different port to avoid conflicts

class TestServer:
    def __init__(self):
        self.server = ReliableUDP(timeout=2.0, loss_rate=0.0)  # Disable loss simulation for tests
        self.server.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind((HOST, PORT))
            logger.info(f"Server bound to {HOST}:{PORT}")
        except Exception as e:
            logger.error(f"Failed to bind server: {e}")
            raise
            
        self.running = threading.Event()
        self.running.set()
        self.thread = threading.Thread(target=self.handler, daemon=True)
        self.server_ready = threading.Event()

    def start(self):
        logger.info("Starting server...")
        self.thread.start()
        
        # Signal when server is ready instead of using sleep
        countdown = 10
        while not self.server_ready.is_set() and countdown > 0:
            time.sleep(0.2)
            countdown -= 1
            
        if not self.server_ready.is_set():
            logger.warning("Server startup may not be complete!")
        else:
            logger.info("Server ready")

    def stop(self):
        logger.info("Stopping server...")
        self.running.clear()
        
        if hasattr(self, 'server') and self.server:
            self.server.close()
            
        if self.thread.is_alive():
            self.thread.join(timeout=2)
            logger.info("Server thread stopped")

    def handler(self):
        logger.info("Server handler started")
        self.server_ready.set()  # Signal that server is ready
        
        while self.running.is_set():
            try:
                logger.debug("Server waiting for data...")
                request_data, addr = self.server.reliable_recv()
                
                if not request_data:
                    logger.warning("Received empty request data")
                    continue
                    
                request = request_data.decode()
                logger.info(f"[Request from {addr}]\n{request}")

                lines = request.splitlines()
                if not lines:
                    logger.warning("Request contains no lines")
                    continue

                # Parse the request line
                try:
                    method, path, _ = lines[0].split()
                except ValueError:
                    logger.warning(f"Malformed request line: {lines[0]}")
                    method, path = "BAD", "/"

                # Handle different HTTP methods
                if method == "GET":
                    if path == "/":
                        body = "<h1>Welcome to ReliableUDP HTTP Server</h1>"
                        response = (
                            "HTTP/1.0 200 OK\r\n"
                            f"Content-Length: {len(body)}\r\n"
                            "Content-Type: text/html\r\n\r\n"
                            + body
                        )
                    else:
                        response = "HTTP/1.0 404 Not Found\r\nContent-Length: 0\r\n\r\n"
                    
                    logger.info(f"Sending response to {addr}: {response.splitlines()[0]}")
                    self.server.reliable_send(addr, response.encode())

                elif method == "POST":
                    content = request.split("\r\n\r\n", 1)[-1]
                    logger.info(f"Received POST data: {content}")
                    body = "Data received"
                    response = (
                        "HTTP/1.0 200 OK\r\n"
                        f"Content-Length: {len(body)}\r\n"
                        "Content-Type: text/plain\r\n\r\n"
                        + body
                    )
                    logger.info(f"Sending response to {addr}: {response.splitlines()[0]}")
                    self.server.reliable_send(addr, response.encode())

                else:
                    response = "HTTP/1.0 405 Method Not Allowed\r\nContent-Length: 0\r\n\r\n"
                    logger.info(f"Sending response to {addr}: {response.splitlines()[0]}")
                    self.server.reliable_send(addr, response.encode())

            except TimeoutError:
                # Timeout on recvfrom, just continue to check running flag
                continue
            except OSError as e:
                # Socket likely closed during shutdown, exit loop quietly
                if not self.running.is_set() or not hasattr(self, 'server') or not self.server:
                    logger.info("Server shutting down, exiting handler")
                    break
                logger.error(f"Server OSError: {e}")
            except Exception as e:
                if not self.running.is_set():
                    break
                logger.error(f"Server error: {e}")

        logger.info("Server handler exited")


class TestReliableUDPHTTP(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logger.info("Setting up test class...")
        try:
            # Try to find an available port
            cls.test_server = TestServer()
            cls.test_server.start()
        except Exception as e:
            logger.error(f"Error during server setup: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        logger.info("Tearing down test class...")
        try:
            if hasattr(cls, 'test_server'):
                cls.test_server.stop()
                time.sleep(1)  # Allow time for socket to fully close
        except Exception as e:
            logger.error(f"Error during teardown: {e}")

    def setUp(self):
        try:
            self.client = ReliableUDP(timeout=1.0, loss_rate=0.0)  # Shorter timeout for faster tests
            client_addr = (HOST, 0)  # Use dynamic port
            self.client.bind(client_addr)
            logger.info(f"Test client bound to {client_addr[0]}:{self.client.server.getsockname()[1]}")
        except Exception as e:
            logger.error(f"Error setting up client: {e}")
            raise

    def tearDown(self):
        try:
            if hasattr(self, 'client') and self.client:
                self.client.close()
                time.sleep(0.5)  # Allow time for socket to fully close
        except Exception as e:
            logger.error(f"Error tearing down client: {e}")

    def test_get_request(self):
        logger.info("Running test_get_request")
        request = (
            "GET / HTTP/1.0\r\n"
            "Host: 127.0.0.1\r\n"
            "User-Agent: ReliableClient\r\n\r\n"
        )
        success = self.client.reliable_send((HOST, PORT), request.encode())
        self.assertTrue(success, "Failed to send GET request")
        
        response, _ = self.client.reliable_recv()
        response_str = response.decode()
        logger.info(f"Received response: {response_str.splitlines()[0]}")
        self.assertIn("200 OK", response_str)
        self.assertIn("<h1>Welcome", response_str)

    def test_post_request(self):
        logger.info("Running test_post_request")
        request = (
            "POST /submit HTTP/1.0\r\n"
            "Host: 127.0.0.1\r\n"
            "Content-Length: 13\r\n"
            "Content-Type: text/plain\r\n\r\n"
            "Hello, Server!"
        )
        success = self.client.reliable_send((HOST, PORT), request.encode())
        self.assertTrue(success, "Failed to send POST request")
        
        response, _ = self.client.reliable_recv()
        response_str = response.decode()
        logger.info(f"Received response: {response_str.splitlines()[0]}")
        self.assertIn("200 OK", response_str)
        self.assertIn("Data received", response_str)

    def test_404_request(self):
        logger.info("Running test_404_request")
        request = (
            "GET /invalid HTTP/1.0\r\n"
            "Host: 127.0.0.1\r\n\r\n"
        )
        success = self.client.reliable_send((HOST, PORT), request.encode())
        self.assertTrue(success, "Failed to send 404 request")
        
        response, _ = self.client.reliable_recv()
        response_str = response.decode()
        logger.info(f"Received response: {response_str.splitlines()[0]}")
        self.assertIn("404 Not Found", response_str)

    def test_malformed_request(self):
        logger.info("Running test_malformed_request")
        request = (
            "BADREQUEST / HTTP/1.0\r\n"
            "Host: 127.0.0.1\r\n\r\n"
        )
        success = self.client.reliable_send((HOST, PORT), request.encode())
        self.assertTrue(success, "Failed to send malformed request")
        
        response, _ = self.client.reliable_recv()
        response_str = response.decode()
        logger.info(f"Received response: {response_str.splitlines()[0]}")
        self.assertIn("405 Method Not Allowed", response_str)


if __name__ == '__main__':
    # Set a fixed seed for reproducible tests
    random.seed(42)
    
    # Check if port is available
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((HOST, PORT))
        sock.close()
        logger.info(f"Port {PORT} is available")
    except Exception as e:
        logger.error(f"Port {PORT} is not available: {e}")
        print(f"Cannot bind to port {PORT}. Tests will likely fail.")
        
    print("\nRunning tests with enhanced logging. Check the log output for details.\n")
    unittest.main()