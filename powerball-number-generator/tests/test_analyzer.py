#!/usr/bin/env python3
"""Unit tests for statistical analysis functionality"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

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
            },
            {
                'draw_date': '2023-01-10',
                'ball1': 3, 'ball2': 23, 'ball3': 35, 'ball4': 42, 'ball5': 61,
                'powerball': 24, 'multiplier': 4, 'jackpot_amount': 160000000
            },
            {
                'draw_date': '2023-01-13',
                'ball1': 8, 'ball2': 19, 'ball3': 29, 'ball4': 45, 'ball5': 67,
                'powerball': 9, 'multiplier': 2, 'jackpot_amount': 180000000
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
        self.assertEqual(self.analyzer.db_path, self.test_db_path)
    
    def test_get_frequency_analysis(self):
        """Test frequency analysis functionality"""
        analysis = self.analyzer.get_frequency_analysis()
        
        self.assertIn('white_balls', analysis)
        self.assertIn('powerball', analysis)
        
        # Check structure
        white_balls = analysis['white_balls']
        self.assertIsInstance(white_balls, dict)
        
        # Should have frequency data for numbers that appeared
        self.assertIn('12', white_balls)  # Appeared twice
        self.assertEqual(white_balls['12'], 2)
        
        powerball = analysis['powerball']
        self.assertIn('18', powerball)  # Appeared twice
        self.assertEqual(powerball['18'], 2)
    
    def test_get_gap_analysis(self):
        """Test gap analysis functionality"""
        analysis = self.analyzer.get_gap_analysis()
        
        self.assertIn('white_balls', analysis)
        self.assertIn('powerball', analysis)
        
        # Check that gaps are calculated
        white_balls = analysis['white_balls']
        self.assertIsInstance(white_balls, dict)
        
        # Numbers that appeared should have gap of 0
        self.assertIn('12', white_balls)
        self.assertEqual(white_balls['12'], 0)  # Appeared in most recent drawing
    
    def test_get_pattern_analysis(self):
        """Test pattern analysis functionality"""
        analysis = self.analyzer.get_pattern_analysis()
        
        self.assertIn('consecutive_patterns', analysis)
        self.assertIn('sum_ranges', analysis)
        self.assertIn('even_odd_patterns', analysis)
        
        # Check sum ranges
        sum_ranges = analysis['sum_ranges']
        self.assertIn('low', sum_ranges)
        self.assertIn('medium', sum_ranges)
        self.assertIn('high', sum_ranges)
    
    def test_get_position_analysis(self):
        """Test position-based analysis"""
        analysis = self.analyzer.get_position_analysis()
        
        self.assertIn('position_frequencies', analysis)
        self.assertIn('position_averages', analysis)
        
        # Should have 5 positions
        pos_freq = analysis['position_frequencies']
        self.assertEqual(len(pos_freq), 5)
        
        # Each position should have frequency data
        for pos in pos_freq:
            self.assertIsInstance(pos, dict)
    
    def test_comprehensive_analysis(self):
        """Test comprehensive analysis combining all methods"""
        analysis = self.analyzer.get_comprehensive_analysis()
        
        # Should include all analysis types
        self.assertIn('frequency_analysis', analysis)
        self.assertIn('gap_analysis', analysis)
        self.assertIn('pattern_analysis', analysis)
        self.assertIn('position_analysis', analysis)
        self.assertIn('data_summary', analysis)
        
        # Check data summary
        data_summary = analysis['data_summary']
        self.assertIn('total_drawings', data_summary)
        self.assertIn('date_range', data_summary)
        self.assertEqual(data_summary['total_drawings'], 5)
    
    def test_get_hot_cold_numbers(self):
        """Test hot and cold number identification"""
        hot_cold = self.analyzer.get_hot_cold_numbers()
        
        self.assertIn('hot_white_balls', hot_cold)
        self.assertIn('cold_white_balls', hot_cold)
        self.assertIn('hot_powerball', hot_cold)
        self.assertIn('cold_powerball', hot_cold)
        
        # Hot numbers should include frequently appearing ones
        hot_white = hot_cold['hot_white_balls']
        self.assertIsInstance(hot_white, list)
        
        # Should include number 12 (appeared twice)
        hot_numbers = [item['number'] for item in hot_white]
        self.assertIn(12, hot_numbers)
    
    def test_get_overdue_numbers(self):
        """Test overdue number identification"""
        overdue = self.analyzer.get_overdue_numbers()
        
        self.assertIn('white_balls', overdue)
        self.assertIn('powerball', overdue)
        
        # Should return lists of overdue numbers
        white_balls = overdue['white_balls']
        self.assertIsInstance(white_balls, list)
        
        # Should have numbers that haven't appeared
        self.assertGreater(len(white_balls), 0)
    
    def test_calculate_number_probabilities(self):
        """Test probability calculations"""
        probabilities = self.analyzer.calculate_number_probabilities()
        
        self.assertIn('white_balls', probabilities)
        self.assertIn('powerball', probabilities)
        
        # Check that probabilities sum appropriately
        white_probs = probabilities['white_balls']
        self.assertIsInstance(white_probs, dict)
        
        # All probabilities should be between 0 and 1
        for prob in white_probs.values():
            self.assertGreaterEqual(prob, 0)
            self.assertLessEqual(prob, 1)

class TestAnalysisEdgeCases(unittest.TestCase):
    """Test edge cases and error handling in analysis"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_empty.db')
        
        # Create empty database
        collector = PowerballDataCollector(db_path=self.test_db_path)
        collector.setup_database()
        
        self.analyzer = PowerballAnalyzer(db_path=self.test_db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_empty_database_analysis(self):
        """Test analysis with empty database"""
        analysis = self.analyzer.get_frequency_analysis()
        
        # Should handle empty data gracefully
        self.assertIn('white_balls', analysis)
        self.assertIn('powerball', analysis)
        
        # Should return empty or default structures
        self.assertIsInstance(analysis['white_balls'], dict)
        self.assertIsInstance(analysis['powerball'], dict)
    
    def test_insufficient_data_analysis(self):
        """Test analysis with minimal data"""
        # Add just one drawing
        collector = PowerballDataCollector(db_path=self.test_db_path)
        collector.store_drawings([{
            'draw_date': '2023-01-01',
            'ball1': 12, 'ball2': 23, 'ball3': 34, 'ball4': 45, 'ball5': 56,
            'powerball': 18, 'multiplier': 2, 'jackpot_amount': 100000000
        }])
        
        analysis = self.analyzer.get_comprehensive_analysis()
        
        # Should handle minimal data without errors
        self.assertIn('data_summary', analysis)
        self.assertEqual(analysis['data_summary']['total_drawings'], 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)