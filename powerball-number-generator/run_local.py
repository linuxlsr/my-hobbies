#!/usr/bin/env python3
"""Local development server runner"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the PowerballAI application locally"""
    
    print("🎱 PowerballAI Predictor - Local Development Server")
    print("=" * 50)
    
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)
    
    # Check if data exists, if not initialize
    if not os.path.exists('data/powerball.db'):
        print("📊 Initializing database with sample data...")
        subprocess.run([sys.executable, 'cli/powerball_cli.py', 'update-data'])
        print()
    
    # Show status
    print("📈 Current system status:")
    subprocess.run([sys.executable, 'cli/powerball_cli.py', 'status'])
    print()
    
    print("🚀 Starting web server...")
    print("📱 Open your browser to: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop the server")
    print()
    
    # Start Flask development server
    try:
        subprocess.run([sys.executable, 'web/app.py'])
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Thanks for using PowerballAI!")

if __name__ == "__main__":
    main()