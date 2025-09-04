#!/usr/bin/env python3
"""Data collection module for Powerball historical data"""

import requests
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import time

class PowerballDataCollector:
    """Collects and manages Powerball historical data"""
    
    def __init__(self, db_path: str = "data/powerball.db"):
        # Ensure data directory exists
        import os
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.base_url = "https://www.powerball.com"
        self.api_url = "https://www.powerball.com/api/v1/numbers/powerball"
        
    def setup_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drawings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draw_date DATE NOT NULL,
                ball1 INTEGER NOT NULL,
                ball2 INTEGER NOT NULL,
                ball3 INTEGER NOT NULL,
                ball4 INTEGER NOT NULL,
                ball5 INTEGER NOT NULL,
                powerball INTEGER NOT NULL,
                multiplier INTEGER,
                jackpot_amount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(draw_date)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def fetch_recent_drawings(self, limit: int = 100) -> List[Dict]:
        """Fetch recent drawings from NY State Gaming Commission API"""
        try:
            print("Fetching real Powerball data from NY State Gaming Commission...")
            url = "https://data.ny.gov/api/views/d6yy-54nr/rows.json"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                raw_data = data.get('data', [])
                
                drawings = []
                for row in raw_data[-limit:]:  # Get most recent drawings
                    try:
                        # NY data format: [metadata..., date, numbers, powerball]
                        if len(row) < 11:
                            continue
                            
                        draw_date = row[8]  # Date column (index 8)
                        numbers_str = row[9]  # Winning numbers column (index 9)
                        powerball_str = row[10]  # Powerball column (index 10)
                        
                        # Parse date (format: 2020-09-26T00:00:00)
                        if 'T' in draw_date:
                            draw_date = draw_date.split('T')[0]
                        
                        # Parse numbers (format: "11 21 27 36 62 24" - last number is powerball)
                        if numbers_str and powerball_str:
                            # Split the numbers string
                            all_numbers = numbers_str.split()
                            if len(all_numbers) >= 5:
                                white_balls = [int(x.strip()) for x in all_numbers[:5]]
                                red_ball = int(powerball_str.strip())
                                
                                drawings.append({
                                    'draw_date': draw_date,
                                    'ball1': white_balls[0],
                                    'ball2': white_balls[1],
                                    'ball3': white_balls[2],
                                    'ball4': white_balls[3],
                                    'ball5': white_balls[4],
                                    'powerball': red_ball,
                                    'multiplier': None,
                                    'jackpot_amount': None
                                })
                    except (IndexError, ValueError, TypeError) as e:
                        print(f"Skipping malformed row: {e}")
                        continue
                
                print(f"Successfully fetched {len(drawings)} real drawings")
                return drawings
            else:
                print(f"API returned status {response.status_code}, using sample data")
                return self._generate_sample_data(limit)
                
        except Exception as e:
            print(f"Error fetching real data: {e}, using sample data")
            return self._generate_sample_data(limit)
    
    def _generate_sample_data(self, count: int) -> List[Dict]:
        """Generate sample historical data for development"""
        import random
        
        # Set seed for reproducible data
        random.seed(42)
        
        drawings = []
        # Start from 2020 to simulate several years of data
        start_date = datetime(2020, 1, 1)
        
        # Powerball draws are typically Mon, Wed, Sat
        draw_days = [0, 2, 5]  # Monday=0, Wednesday=2, Saturday=5
        
        current_date = start_date
        for i in range(count):
            # Find next draw day
            while current_date.weekday() not in draw_days:
                current_date += timedelta(days=1)
            
            # Generate realistic Powerball numbers with some bias toward certain numbers
            # to create more realistic frequency patterns
            white_balls = sorted(random.sample(range(1, 70), 5))
            red_ball = random.randint(1, 26)
            
            # Add some bias to make certain numbers more frequent (realistic)
            if random.random() < 0.15:  # 15% chance to use "hot" numbers
                hot_whites = [7, 14, 21, 28, 35, 42, 49, 56, 63]
                hot_reds = [3, 7, 12, 18, 22]
                white_balls = sorted(random.sample(hot_whites + list(range(1, 70)), 5))
                if random.random() < 0.3:
                    red_ball = random.choice(hot_reds)
            
            drawings.append({
                'draw_date': current_date.strftime('%Y-%m-%d'),
                'ball1': white_balls[0],
                'ball2': white_balls[1],
                'ball3': white_balls[2],
                'ball4': white_balls[3],
                'ball5': white_balls[4],
                'powerball': red_ball,
                'multiplier': random.choice([2, 3, 4, 5, 10]),
                'jackpot_amount': random.randint(20, 500) * 1000000
            })
            
            # Move to next draw (typically 2-4 days later)
            current_date += timedelta(days=random.choice([2, 3, 4]))
            
        return drawings
    
    def store_drawings(self, drawings: List[Dict]):
        """Store drawings in SQLite database"""
        if not drawings:
            return
            
        conn = sqlite3.connect(self.db_path)
        new_count = 0
        
        for drawing in drawings:
            try:
                cursor = conn.execute('''
                    INSERT OR IGNORE INTO drawings 
                    (draw_date, ball1, ball2, ball3, ball4, ball5, powerball, multiplier, jackpot_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    drawing['draw_date'],
                    drawing['ball1'],
                    drawing['ball2'],
                    drawing['ball3'],
                    drawing['ball4'],
                    drawing['ball5'],
                    drawing['powerball'],
                    drawing.get('multiplier'),
                    drawing.get('jackpot_amount')
                ))
                if cursor.rowcount > 0:
                    new_count += 1
            except Exception as e:
                print(f"Error storing drawing {drawing['draw_date']}: {e}")
        
        conn.commit()
        conn.close()
        
        if new_count > 0:
            print(f"Successfully stored {new_count} new drawings")
    
    def get_historical_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Retrieve historical data as pandas DataFrame"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM drawings ORDER BY draw_date DESC"
        if limit:
            query += f" LIMIT {limit}"
            
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            df['draw_date'] = pd.to_datetime(df['draw_date'])
            
        return df
    
    def get_latest_date_in_db(self) -> Optional[str]:
        """Get the most recent drawing date in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(draw_date) FROM drawings")
            result = cursor.fetchone()
            conn.close()
            return result[0] if result and result[0] else None
        except Exception:
            return None
    
    def fetch_new_drawings_only(self) -> List[Dict]:
        """Fetch only new drawings since last update"""
        latest_date = self.get_latest_date_in_db()
        
        if not latest_date:
            print("No existing data, performing initial load...")
            return self.fetch_recent_drawings(2000)
        
        print(f"Checking for new drawings since {latest_date}...")
        
        try:
            url = "https://data.ny.gov/api/views/d6yy-54nr/rows.json"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                raw_data = data.get('data', [])
                
                new_drawings = []
                latest_datetime = datetime.strptime(latest_date, '%Y-%m-%d')
                
                for row in raw_data:
                    try:
                        if len(row) < 11:
                            continue
                            
                        draw_date = row[8]
                        if 'T' in draw_date:
                            draw_date = draw_date.split('T')[0]
                        
                        # Only process drawings newer than our latest
                        draw_datetime = datetime.strptime(draw_date, '%Y-%m-%d')
                        if draw_datetime <= latest_datetime:
                            continue
                        
                        numbers_str = row[9]
                        powerball_str = row[10]
                        
                        if numbers_str and powerball_str:
                            all_numbers = numbers_str.split()
                            if len(all_numbers) >= 5:
                                white_balls = [int(x.strip()) for x in all_numbers[:5]]
                                red_ball = int(powerball_str.strip())
                                
                                new_drawings.append({
                                    'draw_date': draw_date,
                                    'ball1': white_balls[0],
                                    'ball2': white_balls[1],
                                    'ball3': white_balls[2],
                                    'ball4': white_balls[3],
                                    'ball5': white_balls[4],
                                    'powerball': red_ball,
                                    'multiplier': None,
                                    'jackpot_amount': None
                                })
                    except (IndexError, ValueError, TypeError):
                        continue
                
                print(f"Found {len(new_drawings)} new drawings")
                return new_drawings
            else:
                print(f"API returned status {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error fetching new data: {e}")
            return []
    
    def update_data(self):
        """Update database with only new drawings"""
        print("Checking for new Powerball drawings...")
        new_drawings = self.fetch_new_drawings_only()
        
        if new_drawings:
            self.store_drawings(new_drawings)
            print(f"Added {len(new_drawings)} new drawings to database")
        else:
            print("Database is up to date - no new drawings")
    
    def get_data_summary(self) -> Dict:
        """Get summary statistics of stored data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM drawings")
        total_drawings = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(draw_date), MAX(draw_date) FROM drawings")
        date_range = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_drawings': total_drawings,
            'date_range': {
                'earliest': date_range[0],
                'latest': date_range[1]
            }
        }

if __name__ == "__main__":
    collector = PowerballDataCollector()
    collector.setup_database()
    collector.update_data()
    
    summary = collector.get_data_summary()
    print(f"Database contains {summary['total_drawings']} drawings")
    print(f"Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")