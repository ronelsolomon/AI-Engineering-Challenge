#!/usr/bin/env python3
"""
Helper script to start ngrok tunnel for Twilio webhooks.
Requires ngrok to be installed and NGROK_AUTH_TOKEN in .env
"""
import os
import subprocess
import sys
from config import SERVER_PORT, NGROK_AUTH_TOKEN

def start_ngrok():
    if not NGROK_AUTH_TOKEN or NGROK_AUTH_TOKEN == "your_ngrok_token":
        print("Please set NGROK_AUTH_TOKEN in .env file")
        print("Get your token from https://dashboard.ngrok.com/get-started/your-authtoken")
        sys.exit(1)
    
    print(f"Starting ngrok tunnel on port {SERVER_PORT}...")
    cmd = [
        "ngrok", "http", str(SERVER_PORT),
        "--authtoken", NGROK_AUTH_TOKEN,
        "--log", "stdout"
    ]
    
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"Ngrok started (PID: {process.pid})")
        print("Press Ctrl+C to stop")
        process.wait()
    except FileNotFoundError:
        print("ngrok not found. Please install from https://ngrok.com/download")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopping ngrok...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    start_ngrok()
