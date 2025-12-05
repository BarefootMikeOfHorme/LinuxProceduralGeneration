"""
Backend startup script with port conflict handling
"""
import socket
import subprocess
import sys
import time
import os
from pathlib import Path

PORT = 8000

def is_port_in_use(port):
    """Check if a port is already in use"""
    # Validate port number
    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError(f"Invalid port number: {port}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except socket.error:
            return True

def kill_process_on_port(port):
    """Kill process using the specified port (SECURE - no shell injection)"""
    try:
        # Validate port number to prevent injection
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError(f"Invalid port number: {port}")

        # Use list format to prevent shell injection
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            check=False
        )

        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    try:
                        pid = int(parts[-1])  # Validate PID is integer
                        print(f"Killing process {pid} on port {port}...")
                        # Use list format - no shell injection possible
                        subprocess.run(
                            ['taskkill', '/F', '/PID', str(pid)],
                            capture_output=True,
                            check=False
                        )
                        time.sleep(1)
                        return True
                    except (ValueError, IndexError):
                        continue
        return False
    except Exception as e:
        print(f"Error killing process: {e}")
        return False

def start_backend():
    """Start the backend server"""
    print("=" * 60)
    print("VaultMind Forge - Backend Startup")
    print("=" * 60)
    print()

    # Check if port is in use
    if is_port_in_use(PORT):
        print(f"⚠️  Port {PORT} is already in use!")
        response = input(f"Kill the existing process and restart? (y/n): ")

        if response.lower() == 'y':
            if kill_process_on_port(PORT):
                print(f"✓ Killed existing process on port {PORT}")
                time.sleep(2)
            else:
                print(f"✗ Could not kill process on port {PORT}")
                print(f"Please manually close the application using port {PORT}")
                sys.exit(1)
        else:
            print("Startup cancelled")
            sys.exit(0)

    # Start the backend
    print(f"Starting backend on port {PORT}...")
    print()

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    # Import and run uvicorn
    try:
        import uvicorn
        from api import app

        print("✓ Backend starting...")
        print(f"✓ API: http://localhost:{PORT}")
        print(f"✓ Health: http://localhost:{PORT}/api/health")
        print()

        uvicorn.run(app, host="0.0.0.0", port=PORT)
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error starting backend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_backend()
