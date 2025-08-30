#!/usr/bin/env python3
"""Restart the local MCP server with updated code"""

import subprocess
import time
import requests
import os
import signal

def restart_server():
    """Restart the local MCP server"""
    
    print("🔄 Restarting local MCP server...")
    
    # Try to stop any existing server
    try:
        # Find and kill existing server process
        result = subprocess.run(['pgrep', '-f', 'mcp_server.py'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"Stopping existing server (PID: {pid})")
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(2)
    except Exception as e:
        print(f"Note: {e}")
    
    # Start new server
    print("Starting new server...")
    try:
        # Start server in background
        process = subprocess.Popen(
            ['python3', 'src/mcp_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Test if server is running
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server restarted successfully")
            print("🧪 Testing CloudTrail fix...")
            
            # Test CloudTrail function
            test_response = requests.post("http://localhost:8000/mcp", json={
                "method": "analyze_cloudtrail_events",
                "params": {
                    "instance_id": "i-02cda701eb446f378",
                    "event_types": [],
                    "time_range": "24h"
                }
            }, timeout=30)
            
            if test_response.status_code == 200:
                data = test_response.json()
                if "error" in data:
                    print(f"❌ Still has error: {data['error']}")
                else:
                    print("✅ CloudTrail function working!")
                    events = len(data.get('events', []))
                    print(f"   Found {events} events")
            else:
                print(f"❌ Test failed: {test_response.status_code}")
        else:
            print("❌ Server health check failed")
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")

if __name__ == "__main__":
    restart_server()