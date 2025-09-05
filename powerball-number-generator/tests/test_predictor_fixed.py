#!/usr/bin/env python3
"""Fixed unit tests for predictor functionality"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from predictor import PowerballPredictor
from data_collector import PowerballDataCollector

class TestPowerballPredictor(unittest.TestCase):
    """Test prediction functionality"""
    
    def setUp(self):
        """Set up test environment with sample data"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_powerball.db')
        
        # Create collector and setup database with sample data
        collector = PowerballDataCollector(db_path=self.test_db_path)
        collector.setup_database()
        
        # Create comprehensive sample data for better predictions
        sample_drawings = []
        for i in range(50):  # Create 50 sample drawings
            drawing = {
                'draw_date': f'2023-{(i//30)+1:02d}-{(i%30)+1:02d}',
                'ball1': (i * 7 + 5) % 69 + 1,
                'ball2': (i * 11 + 10) % 69 + 1,
                'ball3': (i * 13 + 15) % 69 + 1,
                'ball4': (i * 17 + 20) % 69 + 1,
                'ball5': (i * 19 + 25) % 69 + 1,
                'powerball': (i * 3 + 1) % 26 + 1,
                'multiplier': (i % 4) + 2,
                'jackpot_amount': 100000000 + (i * 10000000)
            }
            sample_drawings.append(drawing)
        
        collector.store_drawings(sample_drawings)
        
        # Initialize predictor
        self.predictor = PowerballPredictor(db_path=self.test_db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_predictor_initialization(self):
        """Test predictor initialization"""
        self.assertIsNotNone(self.predictor)
        self.assertIsNotNone(self.predictor.analyzer)
    
    def test_generate_single_prediction(self):
        """Test single prediction generation"""
        result = self.predictor.generate_predictions(num_tickets=1)
        
        if 'error' not in result:
            self.assertIn('predictions', result)
            prediction = result['predictions'][0]
            
            # Check structure
            self.assertIn('numbers', prediction)
            self.assertIn('powerball', prediction)
            self.assertIn('confidence_score', prediction)
            self.assertIn('strategy', prediction)
            
            # Validate numbers
            numbers = prediction['numbers']
            self.assertEqual(len(numbers), 5)
            self.assertEqual(len(set(numbers)), 5)  # No duplicates
            
            for num in numbers:
                self.assertGreaterEqual(num, 1)
                self.assertLessEqual(num, 69)
            
            # Validate powerball
            powerball = prediction['powerball']
            self.assertGreaterEqual(powerball, 1)
            self.assertLessEqual(powerball, 26)
    
    def test_all_prediction_strategies(self):
        """Test all prediction strategies"""
        strategies = ['balanced', 'frequency_based', 'gap_based', 'monte_carlo', 'pattern_based']
        
        for strategy in strategies:
            with self.subTest(strategy=strategy):
                result = self.predictor.generate_predictions(num_tickets=1, strategy=strategy)
                
                if 'error' not in result:
                    prediction = result['predictions'][0]
                    self.assertEqual(prediction['strategy'], strategy)
                    self.assertIn('numbers', prediction)
                    self.assertIn('powerball', prediction)
    
    def test_portfolio_generation(self):
        """Test portfolio prediction generation"""
        result = self.predictor.generate_predictions(num_tickets=5, strategy='portfolio')
        
        if 'error' not in result:
            portfolio = result['predictions']
            self.assertEqual(len(portfolio), 5)
            
            # Should use different strategies
            strategies = [pred['strategy'] for pred in portfolio]
            self.assertGreater(len(set(strategies)), 1)
    
    def test_number_validation(self):
        """Test that generated numbers are always valid"""
        result = self.predictor.generate_predictions(num_tickets=5)
        
        if 'error' not in result:
            for prediction in result['predictions']:
                # Check white ball ranges
                for num in prediction['numbers']:
                    self.assertGreaterEqual(num, 1)
                    self.assertLessEqual(num, 69)
                
                # Check powerball range
                pb = prediction['powerball']
                self.assertGreaterEqual(pb, 1)
                self.assertLessEqual(pb, 26)
                
                # Check no duplicates
                self.assertEqual(len(prediction['numbers']), 5)
                self.assertEqual(len(set(prediction['numbers'])), 5)

if __name__ == '__main__':
    unittest.main(verbosity=2)