import os
import asyncio
import websockets
import paramiko
import logging
import re
import base64
import socket
from flask import Flask
from threading import Thread

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("wstunnel.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
PORT = int(os.environ.get("PORT", 80))
HOST = "0.0.0.0"
ALLOWED_USERS = {"dev": "123"}  # Fixed credentials
TCP_BUFFER_SIZE = 1048576  # 1MB for high speed
SOCKET_TIMEOUT = 10
SSH_USER = os.environ.get("SSH_USER", "dev")
SSH_PASS = os.environ.get("SSH_PASS", "123")

# Flask app for Railway (served by Gunicorn)
app = Flask(__name__)

@app.route('/')
def index():
    return "WebSocket SSH Tunnel Server Running"

# Start SSH server
def start_sshd():
    try:
        # Ensure SSH user exists and set password
        os.system(f"echo '{SSH_USER}:{SSH_PASS}' | chpasswd")
        # Start sshd
        os.system("/usr/sbin/sshd -D -e &")
        logger.info("Started SSH server on localhost:22")
    except Exception as e:
        logger.error(f"Failed to start SSH server: {str(e)}")

# WebSocket server
async def handle_websocket(websocket, path):
    logger.debug(f"New WebSocket connection: {path}")
    
    # Parse authentication
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
        
        # Handle WebSocket upgrade (matches DarkTunnel request)
        if "Upgrade" in headers and headers["Upgrade"].lower() == "websocket" and \
           "Host" in headers and "config.rcs.mnc857.mcc405.pub.3gppnetwork.org" in headers["Host"]:
            logger.debug("WebSocket upgrade request from DarkTunnel received")
        
        # SSH tunneling to localhost:22
        async def forward_ssh():
            sock = None
            transport = None
            channel = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(SOCKET_TIMEOUT)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, TCP_BUFFER_SIZE)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, TCP_BUFFER_SIZE)
                sock.connect(("localhost", 22))
                
                transport = paramiko.Transport(sock)
                transport.start_client(timeout=10)
                transport.auth_password(SSH_USER, SSH_PASS)
                channel = transport.open_session()
                
                logger.info(f"SSH channel established for {username}")
                
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

# Start WebSocket server on a different port or handle dynamically
def start_websocket_server():
    # Use a different port or integrate with Gunicorn (e.g., via ASGI)
    async def run_server():
        # Attempt to use PORT, but handle conflict with Gunicorn
        try:
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
        except OSError as e:
            if e.errno == 98:  # Address already in use
                logger.error(f"Port {PORT} already in use by Gunicorn. WebSocket server failed to start.")
            else:
                logger.error(f"WebSocket server error: {str(e)}")
    
    asyncio.run(run_server())

# Main function (run by Gunicorn, not directly)
def main():
    # Start SSH server
    start_sshd()
    # Start WebSocket server (will fail if port conflicts, logged)
    ws_thread = Thread(target=start_websocket_server, daemon=True)
    ws_thread.start()
    # Flask app is served by Gunicorn, so don't run app.run here
    logger.info(f"Flask app ready to be served by Gunicorn on {HOST}:{PORT}")

if __name__ == "__main__":
    # For local testing only
    main()