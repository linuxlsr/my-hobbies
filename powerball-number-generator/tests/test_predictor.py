#!/usr/bin/env python3
"""Unit tests for prediction functionality"""

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
        self.assertEqual(self.predictor.db_path, self.test_db_path)
    
    def test_generate_single_prediction(self):
        """Test single prediction generation"""
        prediction = self.predictor.generate_prediction()
        
        # Check structure
        self.assertIn('numbers', prediction)
        self.assertIn('powerball', prediction)
        self.assertIn('confidence_score', prediction)
        self.assertIn('strategy', prediction)
        self.assertIn('reasoning', prediction)
        
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
        
        # Validate confidence score
        confidence = prediction['confidence_score']
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_all_prediction_strategies(self):
        """Test all prediction strategies"""
        strategies = ['balanced', 'frequency_based', 'gap_based', 'monte_carlo', 'pattern_based']
        
        for strategy in strategies:
            with self.subTest(strategy=strategy):
                prediction = self.predictor.generate_prediction(strategy=strategy)
                
                self.assertEqual(prediction['strategy'], strategy)
                self.assertIn('numbers', prediction)
                self.assertIn('powerball', prediction)
                self.assertIn('confidence_score', prediction)
                
                # Validate number ranges
                for num in prediction['numbers']:
                    self.assertGreaterEqual(num, 1)
                    self.assertLessEqual(num, 69)
                
                self.assertGreaterEqual(prediction['powerball'], 1)
                self.assertLessEqual(prediction['powerball'], 26)
    
    def test_multiple_predictions(self):
        """Test generating multiple predictions"""
        predictions = self.predictor.generate_multiple_predictions(count=5)
        
        self.assertEqual(len(predictions), 5)
        
        for prediction in predictions:
            self.assertIn('numbers', prediction)
            self.assertIn('powerball', prediction)
            self.assertIn('confidence_score', prediction)
            self.assertIn('strategy', prediction)
    
    def test_portfolio_generation(self):
        """Test portfolio prediction generation"""
        portfolio = self.predictor.generate_portfolio(count=5)
        
        self.assertEqual(len(portfolio), 5)
        
        # Should use different strategies
        strategies = [pred['strategy'] for pred in portfolio]
        self.assertGreater(len(set(strategies)), 1)
        
        # All predictions should be valid
        for prediction in portfolio:
            self.assertEqual(len(prediction['numbers']), 5)
            self.assertEqual(len(set(prediction['numbers'])), 5)  # No duplicates
    
    def test_frequency_based_strategy(self):
        """Test frequency-based prediction strategy"""
        prediction = self.predictor._frequency_based_prediction()
        
        self.assertIn('numbers', prediction)
        self.assertIn('powerball', prediction)
        self.assertIn('reasoning', prediction)
        
        # Should mention frequency in reasoning
        self.assertIn('frequent', prediction['reasoning'].lower())
    
    def test_gap_based_strategy(self):
        """Test gap-based prediction strategy"""
        prediction = self.predictor._gap_based_prediction()
        
        self.assertIn('numbers', prediction)
        self.assertIn('powerball', prediction)
        self.assertIn('reasoning', prediction)
        
        # Should mention overdue or gap in reasoning
        reasoning = prediction['reasoning'].lower()
        self.assertTrue('overdue' in reasoning or 'gap' in reasoning)
    
    def test_pattern_based_strategy(self):
        """Test pattern-based prediction strategy"""
        prediction = self.predictor._pattern_based_prediction()
        
        self.assertIn('numbers', prediction)
        self.assertIn('powerball', prediction)
        self.assertIn('reasoning', prediction)
        
        # Should mention pattern in reasoning
        self.assertIn('pattern', prediction['reasoning'].lower())
    
    def test_monte_carlo_strategy(self):
        """Test Monte Carlo prediction strategy"""
        prediction = self.predictor._monte_carlo_prediction()
        
        self.assertIn('numbers', prediction)
        self.assertIn('powerball', prediction)
        self.assertIn('reasoning', prediction)
        
        # Should mention simulation in reasoning
        reasoning = prediction['reasoning'].lower()
        self.assertTrue('simulation' in reasoning or 'monte carlo' in reasoning)
    
    def test_balanced_strategy(self):
        """Test balanced prediction strategy"""
        prediction = self.predictor._balanced_prediction()
        
        self.assertIn('numbers', prediction)
        self.assertIn('powerball', prediction)
        self.assertIn('reasoning', prediction)
        
        # Should mention balanced approach
        self.assertIn('balanced', prediction['reasoning'].lower())
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation"""
        prediction = self.predictor.generate_prediction()
        confidence = prediction['confidence_score']
        
        # Should be reasonable confidence (not too high for lottery)
        self.assertGreaterEqual(confidence, 0.3)
        self.assertLessEqual(confidence, 0.9)
    
    def test_prediction_uniqueness(self):
        """Test that predictions are reasonably unique"""
        predictions = []
        for _ in range(10):
            pred = self.predictor.generate_prediction()
            predictions.append(tuple(sorted(pred['numbers']) + [pred['powerball']]))
        
        # Should have some variety (not all identical)
        unique_predictions = set(predictions)
        self.assertGreater(len(unique_predictions), 1)
    
    def test_invalid_strategy_fallback(self):
        """Test fallback for invalid strategy"""
        prediction = self.predictor.generate_prediction(strategy='invalid_strategy')
        
        # Should fallback to balanced strategy
        self.assertEqual(prediction['strategy'], 'balanced')
    
    def test_prediction_with_insufficient_data(self):
        """Test prediction with minimal data"""
        # Create predictor with minimal data
        temp_db = os.path.join(self.temp_dir, 'minimal.db')
        collector = PowerballDataCollector(db_path=temp_db)
        collector.setup_database()
        
        # Add just one drawing
        collector.store_drawings([{
            'draw_date': '2023-01-01',
            'ball1': 12, 'ball2': 23, 'ball3': 34, 'ball4': 45, 'ball5': 56,
            'powerball': 18, 'multiplier': 2, 'jackpot_amount': 100000000
        }])
        
        minimal_predictor = PowerballPredictor(db_path=temp_db)
        prediction = minimal_predictor.generate_prediction()
        
        # Should still generate valid prediction
        self.assertIn('numbers', prediction)
        self.assertIn('powerball', prediction)
        self.assertEqual(len(prediction['numbers']), 5)

class TestPredictionValidation(unittest.TestCase):
    """Test prediction validation and edge cases"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_powerball.db')
        
        # Create minimal setup
        collector = PowerballDataCollector(db_path=self.test_db_path)
        collector.setup_database()
        
        # Add some basic data
        sample_drawings = [
            {
                'draw_date': '2023-01-01',
                'ball1': 12, 'ball2': 23, 'ball3': 34, 'ball4': 45, 'ball5': 56,
                'powerball': 18, 'multiplier': 2, 'jackpot_amount': 100000000
            }
        ]
        collector.store_drawings(sample_drawings)
        
        self.predictor = PowerballPredictor(db_path=self.test_db_path)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_number_range_validation(self):
        """Test that generated numbers are always in valid ranges"""
        for _ in range(20):  # Test multiple times
            prediction = self.predictor.generate_prediction()
            
            # Check white ball ranges
            for num in prediction['numbers']:
                self.assertGreaterEqual(num, 1, f"White ball {num} below minimum")
                self.assertLessEqual(num, 69, f"White ball {num} above maximum")
            
            # Check powerball range
            pb = prediction['powerball']
            self.assertGreaterEqual(pb, 1, f"Powerball {pb} below minimum")
            self.assertLessEqual(pb, 26, f"Powerball {pb} above maximum")
    
    def test_no_duplicate_white_balls(self):
        """Test that white balls are always unique"""
        for _ in range(20):  # Test multiple times
            prediction = self.predictor.generate_prediction()
            numbers = prediction['numbers']
            
            self.assertEqual(len(numbers), 5, "Should have exactly 5 white balls")
            self.assertEqual(len(set(numbers)), 5, "White balls should be unique")
    
    def test_prediction_structure_consistency(self):
        """Test that prediction structure is always consistent"""
        required_keys = ['numbers', 'powerball', 'confidence_score', 'strategy', 'reasoning']
        
        for strategy in ['balanced', 'frequency_based', 'gap_based', 'monte_carlo', 'pattern_based']:
            prediction = self.predictor.generate_prediction(strategy=strategy)
            
            for key in required_keys:
                self.assertIn(key, prediction, f"Missing key '{key}' in {strategy} prediction")
            
            # Check types
            self.assertIsInstance(prediction['numbers'], list)
            self.assertIsInstance(prediction['powerball'], int)
            self.assertIsInstance(prediction['confidence_score'], float)
            self.assertIsInstance(prediction['strategy'], str)
            self.assertIsInstance(prediction['reasoning'], str)

if __name__ == '__main__':
    unittest.main(verbosity=2)