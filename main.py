#!/usr/bin/env python3
"""
Simple web application with HTTP server and Socket server
HTTP server runs on port 3000
Socket server runs on port 5001
"""

import http.server
import socketserver
import socket
import json
import os
import multiprocessing
import urllib.parse
from datetime import datetime
from pymongo import MongoClient


# Configuration
HTTP_PORT = 3000
SOCKET_PORT = 5001
FRONT_DIR = "front-init"
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DB = "messages_db"
MONGO_COLLECTION = "messages"


class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONT_DIR, **kwargs)

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        # Route handling
        if path == "/" or path == "/index.html":
            self.serve_file("index.html")
        elif path == "/message.html":
            self.serve_file("message.html")
        elif path == "/style.css":
            self.serve_file("style.css", content_type="text/css")
        elif path == "/logo.png":
            self.serve_file("logo.png", content_type="image/png")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == "/message":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            form_data = urllib.parse.parse_qs(post_data.decode("utf-8"))

            username = form_data.get("username", [""])[0]
            message = form_data.get("message", [""])[0]

            if username and message:
                # Send data to socket server
                try:
                    self.send_to_socket_server(username, message)
                    # Redirect to success page or return success response
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"Message sent successfully!")
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(f"Error: {str(e)}".encode())
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"Username and message are required")
        else:
            self.send_error(404, "Not Found")

    def send_to_socket_server(self, username, message):
        """Send data to socket server"""
        data = {
            "username": username,
            "message": message
        }
        json_data = json.dumps(data).encode("utf-8")

        # Connect to socket server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(("localhost", SOCKET_PORT))
            sock.sendall(json_data)
        finally:
            sock.close()

    def serve_file(self, filename, content_type="text/html"):
        """Serve a file from the front-init directory"""
        filepath = os.path.join(FRONT_DIR, filename)
        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.end_headers()
            with open(filepath, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Not Found")

    def send_error(self, code, message=None):
        """Override to serve error.html for 404 errors"""
        if code == 404:
            error_file = os.path.join(FRONT_DIR, "error.html")
            if os.path.exists(error_file):
                self.send_response(404)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                with open(error_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                super().send_error(code, message)
        else:
            super().send_error(code, message)

    def log_message(self, format, *args):
        """Override to customize log messages"""
        pass  # Suppress default logging


def socket_server():
    """Socket server that receives data and saves to MongoDB"""
    # Connect to MongoDB with retry mechanism
    import time
    client = None
    max_retries = 30
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/", serverSelectionTimeoutMS=2000)
            # Test connection
            client.server_info()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Waiting for MongoDB... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print(f"Error connecting to MongoDB after {max_retries} attempts: {e}")
                return
    
    if client is None:
        print("Failed to connect to MongoDB")
        return
    
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]
    print(f"Connected to MongoDB at {MONGO_HOST}:{MONGO_PORT}")

    # Create TCP socket server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", SOCKET_PORT))
    server_socket.listen(5)
    print(f"Socket server listening on port {SOCKET_PORT}")

    while True:
        try:
            client_socket, address = server_socket.accept()
            print(f"Connection from {address}")

            # Receive data
            data = b""
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                data += chunk

            # Parse JSON data
            try:
                json_data = json.loads(data.decode("utf-8"))
                username = json_data.get("username", "")
                message = json_data.get("message", "")

                # Create document with current datetime
                document = {
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "username": username,
                    "message": message
                }

                # Save to MongoDB
                collection.insert_one(document)
                print(f"Saved message: {document}")

            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
            except Exception as e:
                print(f"Error saving to MongoDB: {e}")

            client_socket.close()

        except Exception as e:
            print(f"Error in socket server: {e}")


def http_server():
    """HTTP server function"""
    handler = HTTPRequestHandler
    with socketserver.TCPServer(("", HTTP_PORT), handler) as httpd:
        print(f"HTTP server serving on port {HTTP_PORT}")
        httpd.serve_forever()


def main():
    """Main function to start both servers in separate processes"""
    # Start socket server in a separate process
    socket_process = multiprocessing.Process(target=socket_server)
    socket_process.daemon = True
    socket_process.start()

    # Start HTTP server in main process
    http_server()


if __name__ == "__main__":
    main()

