#!/usr/bin/env python3
"""Clean local database and reload with fresh real data"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def clean_and_reload_data():
    print("🧹 Cleaning local database and reloading with fresh real data")
    
    try:
        from data_collector import PowerballDataCollector
        
        # Remove existing database
        db_path = "data/powerball.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            print("🗑️ Removed old database with mixed real/sample data")
        
        # Create fresh database
        collector = PowerballDataCollector()
        collector.setup_database()
        print("✅ Created fresh database")
        
        # Load only real data
        print("📡 Fetching fresh real data from NY Gaming Authority...")
        real_drawings = collector.fetch_recent_drawings(limit=5000)  # Get more data
        
        # Filter out any future dates (sample data)
        today = datetime.now()
        valid_drawings = []
        
        for drawing in real_drawings:
            try:
                draw_date = datetime.strptime(drawing['draw_date'], '%Y-%m-%d')
                if draw_date <= today:
                    valid_drawings.append(drawing)
                else:
                    print(f"⚠️ Skipping future date: {drawing['draw_date']}")
            except:
                continue
        
        print(f"📊 Filtered to {len(valid_drawings)} valid drawings (no future dates)")
        
        # Store clean data
        collector.store_drawings(valid_drawings)
        
        # Verify
        summary = collector.get_data_summary()
        print(f"✅ Database reloaded:")
        print(f"  Total drawings: {summary['total_drawings']}")
        print(f"  Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
        
        return summary
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == '__main__':
    clean_and_reload_data()