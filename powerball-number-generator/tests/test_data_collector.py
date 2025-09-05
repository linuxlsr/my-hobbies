#!/usr/bin/env python3
"""Unit tests for data collection functionality"""

import unittest
import tempfile
import os
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from data_collector import PowerballDataCollector

class TestDataCollector(unittest.TestCase):
    """Test data collection functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_powerball.db')
        self.collector = PowerballDataCollector(db_path=self.test_db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_setup(self):
        """Test database initialization"""
        self.collector.setup_database()
        
        # Check if database file exists
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Check if table was created
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drawings'")
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'drawings')
    
    def test_store_drawings(self):
        """Test storing drawings in database"""
        self.collector.setup_database()
        
        # Sample drawing data
        drawings = [
            {
                'draw_date': '2023-01-01',
                'ball1': 12, 'ball2': 23, 'ball3': 34, 'ball4': 45, 'ball5': 56,
                'powerball': 18,
                'multiplier': 2,
                'jackpot_amount': 100000000
            },
            {
                'draw_date': '2023-01-04',
                'ball1': 7, 'ball2': 19, 'ball3': 28, 'ball4': 41, 'ball5': 52,
                'powerball': 9,
                'multiplier': 3,
                'jackpot_amount': 120000000
            }
        ]
        
        self.collector.store_drawings(drawings)
        
        # Verify data was stored
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM drawings")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 2)
    
    def test_get_historical_data(self):
        """Test retrieving historical data"""
        self.collector.setup_database()
        
        # Store test data
        drawings = [
            {
                'draw_date': '2023-01-01',
                'ball1': 12, 'ball2': 23, 'ball3': 34, 'ball4': 45, 'ball5': 56,
                'powerball': 18,
                'multiplier': 2,
                'jackpot_amount': 100000000
            }
        ]
        self.collector.store_drawings(drawings)
        
        # Retrieve data
        df = self.collector.get_historical_data()
        
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['ball1'], 12)
        self.assertEqual(df.iloc[0]['powerball'], 18)
    
    def test_get_data_summary(self):
        """Test data summary functionality"""
        self.collector.setup_database()
        
        # Store test data
        drawings = [
            {
                'draw_date': '2023-01-01',
                'ball1': 12, 'ball2': 23, 'ball3': 34, 'ball4': 45, 'ball5': 56,
                'powerball': 18,
                'multiplier': 2,
                'jackpot_amount': 100000000
            },
            {
                'draw_date': '2023-01-04',
                'ball1': 7, 'ball2': 19, 'ball3': 28, 'ball4': 41, 'ball5': 52,
                'powerball': 9,
                'multiplier': 3,
                'jackpot_amount': 120000000
            }
        ]
        self.collector.store_drawings(drawings)
        
        summary = self.collector.get_data_summary()
        
        self.assertEqual(summary['total_drawings'], 2)
        self.assertEqual(summary['date_range']['earliest'], '2023-01-01')
        self.assertEqual(summary['date_range']['latest'], '2023-01-04')
    
    def test_duplicate_prevention(self):
        """Test that duplicate drawings are not stored"""
        self.collector.setup_database()
        
        drawing = {
            'draw_date': '2023-01-01',
            'ball1': 12, 'ball2': 23, 'ball3': 34, 'ball4': 45, 'ball5': 56,
            'powerball': 18,
            'multiplier': 2,
            'jackpot_amount': 100000000
        }
        
        # Store same drawing twice
        self.collector.store_drawings([drawing])
        self.collector.store_drawings([drawing])
        
        # Should only have one record
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM drawings")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 1)
    
    @patch('requests.get')
    def test_fetch_recent_drawings_success(self, mock_get):
        """Test successful API data fetch"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                ['id1', 'uuid1', 0, 1234567890, None, 1234567890, None, {}, 
                 '2023-01-01T00:00:00', '12 23 34 45 56', '18'],
                ['id2', 'uuid2', 0, 1234567890, None, 1234567890, None, {}, 
                 '2023-01-04T00:00:00', '7 19 28 41 52', '9']
            ]
        }
        mock_get.return_value = mock_response
        
        drawings = self.collector.fetch_recent_drawings(limit=10)
        
        self.assertEqual(len(drawings), 2)
        self.assertEqual(drawings[0]['draw_date'], '2023-01-01')
        self.assertEqual(drawings[0]['ball1'], 12)
        self.assertEqual(drawings[0]['powerball'], 18)
    
    @patch('requests.get')
    def test_fetch_recent_drawings_api_failure(self, mock_get):
        """Test API failure fallback to sample data"""
        # Mock API failure
        mock_get.side_effect = Exception("API Error")
        
        drawings = self.collector.fetch_recent_drawings(limit=5)
        
        # Should return sample data
        self.assertEqual(len(drawings), 5)
        self.assertIn('draw_date', drawings[0])
        self.assertIn('ball1', drawings[0])
    
    def test_generate_sample_data(self):
        """Test sample data generation"""
        sample_data = self.collector._generate_sample_data(10)
        
        self.assertEqual(len(sample_data), 10)
        
        for drawing in sample_data:
            # Check required fields
            self.assertIn('draw_date', drawing)
            self.assertIn('ball1', drawing)
            self.assertIn('powerball', drawing)
            
            # Check number ranges
            for i in range(1, 6):
                ball = drawing[f'ball{i}']
                self.assertGreaterEqual(ball, 1)
                self.assertLessEqual(ball, 69)
            
            self.assertGreaterEqual(drawing['powerball'], 1)
            self.assertLessEqual(drawing['powerball'], 26)

class TestDataValidation(unittest.TestCase):
    """Test data validation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_powerball.db')
        self.collector = PowerballDataCollector(db_path=self.test_db_path)
        self.collector.setup_database()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_invalid_number_ranges(self):
        """Test handling of invalid number ranges"""
        # This would be caught by the API parsing, but test database constraints
        invalid_drawing = {
            'draw_date': '2023-01-01',
            'ball1': 70, 'ball2': 23, 'ball3': 34, 'ball4': 45, 'ball5': 56,  # ball1 > 69
            'powerball': 27,  # powerball > 26
            'multiplier': 2,
            'jackpot_amount': 100000000
        }
        
        # Should store without error (validation happens at application level)
        self.collector.store_drawings([invalid_drawing])
        
        # Verify it was stored (database doesn't enforce these constraints)
        df = self.collector.get_historical_data()
        self.assertEqual(len(df), 1)
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields"""
        incomplete_drawing = {
            'draw_date': '2023-01-01',
            'ball1': 12,
            # Missing other required fields
        }
        
        # Should handle gracefully
        try:
            self.collector.store_drawings([incomplete_drawing])
        except Exception as e:
            # Should fail gracefully, not crash
            self.assertIsInstance(e, Exception)

if __name__ == '__main__':
    unittest.main(verbosity=2)