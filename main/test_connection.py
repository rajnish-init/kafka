#!/usr/bin/env python3
"""Simple network connectivity test for Kafka broker."""

import socket
import sys
from config import BOOTSTRAP_SERVER

def test_connection(host: str, port: int, timeout: int = 10) -> bool:
    """Test TCP connection to host:port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

def main():
    """Test connectivity to all configured Kafka brokers."""
    # Parse the bootstrap server
    host, port_str = BOOTSTRAP_SERVER.split(':')
    port = int(port_str)
    
    print(f"Testing connection to {host}:{port}...")
    
    if test_connection(host, port):
        print(f"✓ Successfully connected to {host}:{port}")
        return 0
    else:
        print(f"✗ Failed to connect to {host}:{port}")
        
        # Test other IPs from values.yaml
        other_ips = ["13.82.136.111", "172.191.54.0"]
        for ip in other_ips:
            print(f"Testing alternative IP {ip}:{port}...")
            if test_connection(ip, port):
                print(f"✓ Successfully connected to {ip}:{port}")
                print(f"Consider updating config.py to use {ip}:{port}")
                return 0
            else:
                print(f"✗ Failed to connect to {ip}:{port}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
