import os
import asyncio
import websockets
import paramiko
import logging
<<<<<<< HEAD
import re
import base64
import socket
from flask import Flask
from threading import Thread
=======
from flask import Flask
from threading import Thread
import re
import base64
import socket
import time
import platform
>>>>>>> f813555a5cc6128b2f397a91f715f32803c43978

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("wstunnel.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
<<<<<<< HEAD
PORT = int(os.environ.get("PORT", 80))
HOST = "0.0.0.0"
ALLOWED_USERS = {"dev": "123"}  # Fixed credentials
TCP_BUFFER_SIZE = 1048576  # 1MB for high speed
SOCKET_TIMEOUT = 10
SSH_USER = os.environ.get("SSH_USER", "dev")
SSH_PASS = os.environ.get("SSH_PASS", "123")
=======
PORT = int(os.environ.get("PORT", 8080))  # Default to 8080 for local testing
HOST = "0.0.0.0"
ALLOWED_USERS = {
    "admin": "password123"  # Replace with secure credentials in production
}
TCP_BUFFER_SIZE = 1048576  # 1MB for high-speed
SOCKET_TIMEOUT = 10

# Windows compatibility for socket options
if platform.system() == "Windows":
    import ctypes
    def set_socket_buffer(sock):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, TCP_BUFFER_SIZE)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, TCP_BUFFER_SIZE)
        except Exception as e:
            logger.warning(f"Failed to set socket buffer sizes on Windows: {str(e)}")
else:
    def set_socket_buffer(sock):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, TCP_BUFFER_SIZE)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, TCP_BUFFER_SIZE)
>>>>>>> f813555a5cc6128b2f397a91f715f32803c43978

# Flask app for Railway
app = Flask(__name__)

@app.route('/')
def index():
    return "WebSocket SSH Tunnel Server Running"

<<<<<<< HEAD
# Start SSH server
def start_sshd():
    try:
        # Ensure SSH user exists and set password
        os.system(f"echo '{SSH_USER}:{SSH_PASS}' | chpasswd")
        # Start sshd
        os.system("/usr/sbin/sshd -D -e &")
        logger.info("Started SSH server")
    except Exception as e:
        logger.error(f"Failed to start SSH server: {str(e)}")

=======
>>>>>>> f813555a5cc6128b2f397a91f715f32803c43978
# WebSocket server
async def handle_websocket(websocket, path):
    logger.debug(f"New WebSocket connection: {path}")
    
<<<<<<< HEAD
    # Parse authentication
=======
    # Parse authentication from URL or headers
>>>>>>> f813555a5cc6128b2f397a91f715f32803c43978
    auth = None
    try:
        headers = websocket.request_headers
        if "Authorization" in headers:
            auth_header = headers["Authorization"]
            if auth_header.startswith("Basic "):
                auth = base64.b64decode(auth_header[6:]).decode('utf-8').split(':')
        elif path.startswith("/"):
            match = re.match(r"/([^:]+):([^@]+)@?", path)
            if match:
                auth = [match.group(1), match.group(2)]
        
        if not auth or len(auth) != 2:
            logger.warning("No authentication provided")
            await websocket.close(1008, "Authentication required")
            return
        
        username, password = auth
        if username not in ALLOWED_USERS or ALLOWED_USERS[username] != password:
            logger.warning(f"Invalid credentials for {username}")
            await websocket.close(1008, "Invalid credentials")
            return
        
        logger.info(f"Authenticated user: {username}")
        
<<<<<<< HEAD
        # Handle WebSocket upgrade
=======
        # Handle WebSocket upgrade request
>>>>>>> f813555a5cc6128b2f397a91f715f32803c43978
        if "Upgrade" in headers and headers["Upgrade"].lower() == "websocket":
            logger.debug("WebSocket upgrade request received")
        
        # SSH tunneling
        async def forward_ssh():
            sock = None
            transport = None
            channel = None
            try:
<<<<<<< HEAD
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(SOCKET_TIMEOUT)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, TCP_BUFFER_SIZE)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, TCP_BUFFER_SIZE)
                sock.connect(("localhost", 22))
                
                transport = paramiko.Transport(sock)
                transport.start_client(timeout=10)
                transport.auth_password(SSH_USER, SSH_PASS)
=======
                # Create socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(SOCKET_TIMEOUT)
                set_socket_buffer(sock)
                # Connect to SSH server (localhost for testing, replace with remote host in production)
                ssh_host = os.environ.get("SSH_HOST", "localhost")
                ssh_port = int(os.environ.get("SSH_PORT", 22))
                sock.connect((ssh_host, ssh_port))
                
                # Set up SSH transport
                transport = paramiko.Transport(sock)
                transport.start_client(timeout=10)
                transport.auth_none(username)  # Use WebSocket auth for SSH (adjust for production)
>>>>>>> f813555a5cc6128b2f397a91f715f32803c43978
                channel = transport.open_session()
                
                logger.info(f"SSH channel established for {username}")
                
<<<<<<< HEAD
=======
                # Bidirectional data forwarding
>>>>>>> f813555a5cc6128b2f397a91f715f32803c43978
                async def ws_to_ssh():
                    while True:
                        try:
                            data = await websocket.recv()
                            channel.send(data)
                        except websockets.exceptions.ConnectionClosed:
                            break
                        except Exception as e:
                            logger.error(f"WS to SSH error: {str(e)}")
                            break
                
                async def ssh_to_ws():
                    while True:
                        try:
                            data = channel.recv(TCP_BUFFER_SIZE)
                            if not data:
                                break
                            await websocket.send(data)
                        except Exception as e:
                            logger.error(f"SSH to WS error: {str(e)}")
                            break
                
                await asyncio.gather(ws_to_ssh(), ssh_to_ws())
                
            except Exception as e:
                logger.error(f"SSH tunnel error: {str(e)}")
                await websocket.close(1011, str(e))
            finally:
                if channel:
                    channel.close()
                if transport:
                    transport.close()
                if sock:
                    sock.close()
        
        await forward_ssh()
        
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(1011, str(e))

# Start WebSocket server
def start_websocket_server():
    async def run_server():
        server = await websockets.serve(
            handle_websocket,
            HOST,
            PORT,
            max_size=TCP_BUFFER_SIZE,
            ping_interval=20,
            ping_timeout=20
        )
        logger.info(f"WebSocket server started on {HOST}:{PORT}")
        await server.wait_closed()
    
    asyncio.run(run_server())

<<<<<<< HEAD
# Run Flask, WebSocket, and SSH
def main():
    # Start SSH server
    start_sshd()
    # Start WebSocket server
    ws_thread = Thread(target=start_websocket_server, daemon=True)
    ws_thread.start()
    # Start Flask
=======
# Run Flask and WebSocket in separate threads
def main():
    # Start WebSocket server in a thread
    ws_thread = Thread(target=start_websocket_server, daemon=True)
    ws_thread.start()
    
    # Optimize TCP settings (limited on Railway without root)
    if platform.system() != "Windows":
        try:
            os.system("bash config/tcp_optimize.sh")
            logger.info("TCP optimizations applied")
        except Exception as e:
            logger.error(f"TCP optimization error: {str(e)}")
    else:
        logger.info("Skipping TCP optimizations on Windows (run manually on Linux server if needed)")
    
    # Start Flask app
>>>>>>> f813555a5cc6128b2f397a91f715f32803c43978
    logger.info(f"Starting Flask app on {HOST}:{PORT}")
    app.run(host=HOST, port=PORT, threaded=True)

if __name__ == "__main__":
    main()