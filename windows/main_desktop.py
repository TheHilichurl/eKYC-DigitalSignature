"""
eKYC & Digital Signature System - Windows Desktop Pro
Powered by Python, OpenCV Zoo (YuNet + SFace), RSA-2048 PKI, and Edge WebView2
"""

import os
import sys
import time
import socket
import threading
import urllib.request
import webview

# Ensure parent directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

APP_PORT = 8000
SERVER_URL = f"http://127.0.0.1:{APP_PORT}"

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_backend():
    """Start Uvicorn backend in background thread if not already running."""
    import uvicorn
    from app import app
    print(f"[*] Starting local backend server on 127.0.0.1:{APP_PORT}...")
    uvicorn.run(app, host="127.0.0.1", port=APP_PORT, log_level="warning")

def wait_for_server(url: str, timeout: int = 15):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(f"{url}/api/identities", timeout=1) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False

def main():
    print("=" * 60)
    print("   eKYC & DIGITAL SIGNATURE SYSTEM - WINDOWS DESKTOP")
    print("   Theme: Cobalt Blue (#1D4ED8) & Modern Orange (#EA580C)")
    print("   Security: RSA-2048 PKI, SHA-256 PSS, Anti-Tampering")
    print("=" * 60)

    # 1. Start server if not running
    if not is_port_in_use(APP_PORT):
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        print("[*] Waiting for local eKYC engine to initialize...")
        if not wait_for_server(SERVER_URL):
            print("[!] Warning: Local server took longer than expected to initialize.")
    else:
        print(f"[*] Connected to active backend at {SERVER_URL}")

    # 2. Launch Native Windows WebView2 Window
    print("[*] Opening Native Windows Desktop Application...")
    window = webview.create_window(
        title="eKYC Digital Signature - Desktop Workstation Pro",
        url=SERVER_URL,
        width=1320,
        height=880,
        resizable=True,
        min_size=(1024, 700),
        text_select=True,
        confirm_close=False,
        background_color='#0B1120'
    )

    # Start the desktop window (Edge WebView2)
    webview.start(debug=False)
    print("[*] Windows Desktop application closed.")

if __name__ == "__main__":
    main()

