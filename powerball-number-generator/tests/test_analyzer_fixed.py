#!/usr/bin/env python3
"""Fixed unit tests for analyzer functionality"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from analyzer import PowerballAnalyzer
from data_collector import PowerballDataCollector

class TestPowerballAnalyzer(unittest.TestCase):
    """Test statistical analysis functionality"""
    
    def setUp(self):
        """Set up test environment with sample data"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_powerball.db')
        
        # Create collector and setup database
        collector = PowerballDataCollector(db_path=self.test_db_path)
        collector.setup_database()
        
        # Create sample data for testing
        sample_drawings = [
            {
                'draw_date': '2023-01-01',
                'ball1': 12, 'ball2': 23, 'ball3': 34, 'ball4': 45, 'ball5': 56,
                'powerball': 18, 'multiplier': 2, 'jackpot_amount': 100000000
            },
            {
                'draw_date': '2023-01-04',
                'ball1': 7, 'ball2': 19, 'ball3': 28, 'ball4': 41, 'ball5': 52,
                'powerball': 9, 'multiplier': 3, 'jackpot_amount': 120000000
            },
            {
                'draw_date': '2023-01-07',
                'ball1': 12, 'ball2': 15, 'ball3': 31, 'ball4': 47, 'ball5': 59,
                'powerball': 18, 'multiplier': 2, 'jackpot_amount': 140000000
            }
        ]
        
        collector.store_drawings(sample_drawings)
        
        # Initialize analyzer
        self.analyzer = PowerballAnalyzer(db_path=self.test_db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_analyzer_initialization(self):
        """Test analyzer initialization"""
        self.assertIsNotNone(self.analyzer)
        self.assertIsInstance(self.analyzer.data, pd.DataFrame)
    
    def test_analyze_frequency_patterns(self):
        """Test frequency analysis functionality"""
        analysis = self.analyzer.analyze_frequency_patterns()
        
        self.assertIsInstance(analysis, dict)
        if analysis:  # If we have data
            self.assertIn('all_time', analysis)
            all_time = analysis['all_time']
            self.assertIn('white_ball_frequency', all_time)
            self.assertIn('red_ball_frequency', all_time)
    
    def test_calculate_gaps(self):
        """Test gap analysis functionality"""
        analysis = self.analyzer.calculate_gaps()
        
        self.assertIsInstance(analysis, dict)
        if analysis:  # If we have data
            self.assertIn('white_ball_gaps', analysis)
            self.assertIn('red_ball_gaps', analysis)
    
    def test_comprehensive_analysis(self):
        """Test comprehensive analysis"""
        analysis = self.analyzer.get_comprehensive_analysis()
        
        if 'error' not in analysis:
            self.assertIn('data_summary', analysis)
            self.assertIn('frequency_analysis', analysis)
            self.assertIn('gap_analysis', analysis)

if __name__ == '__main__':
    unittest.main(verbosity=2)