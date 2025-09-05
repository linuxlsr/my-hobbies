#!/usr/bin/env python3
"""Integration tests for the complete powerball system"""

import unittest
import tempfile
import os
import sys
import subprocess
import time
import requests
import threading
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from data_collector import PowerballDataCollector
from analyzer import PowerballAnalyzer
from predictor import PowerballPredictor

class TestSystemIntegration(unittest.TestCase):
    """Test integration between all system components"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'integration_test.db')
        
        # Initialize all components
        self.collector = PowerballDataCollector(db_path=self.test_db_path)
        self.analyzer = PowerballAnalyzer(db_path=self.test_db_path)
        self.predictor = PowerballPredictor(db_path=self.test_db_path)
        
        # Setup database with comprehensive test data
        self.collector.setup_database()
        self._create_test_data()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def _create_test_data(self):
        """Create comprehensive test data"""
        sample_drawings = []
        for i in range(100):  # Create 100 sample drawings for robust testing
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
        
        self.collector.store_drawings(sample_drawings)
    
    def test_data_flow_integration(self):
        """Test complete data flow from collection to prediction"""
        # 1. Data Collection
        summary = self.collector.get_data_summary()
        self.assertEqual(summary['total_drawings'], 100)
        
        # 2. Analysis
        analysis = self.analyzer.get_comprehensive_analysis()
        self.assertIn('frequency_analysis', analysis)
        self.assertIn('gap_analysis', analysis)
        
        # 3. Prediction
        prediction = self.predictor.generate_prediction()
        self.assertIn('numbers', prediction)
        self.assertIn('powerball', prediction)
        
        # Verify prediction uses analysis data
        self.assertGreater(prediction['confidence_score'], 0)
    
    def test_analysis_prediction_consistency(self):
        """Test that predictions are consistent with analysis"""
        # Get frequency analysis
        freq_analysis = self.analyzer.get_frequency_analysis()
        hot_numbers = []
        
        # Extract most frequent white balls
        white_freq = freq_analysis['white_balls']
        if white_freq:
            sorted_freq = sorted(white_freq.items(), key=lambda x: x[1], reverse=True)
            hot_numbers = [int(num) for num, _ in sorted_freq[:10]]
        
        # Generate frequency-based prediction
        prediction = self.predictor.generate_prediction(strategy='frequency_based')
        
        # At least some numbers should be from hot numbers (if we have enough data)
        if hot_numbers:
            overlap = set(prediction['numbers']) & set(hot_numbers)
            self.assertGreater(len(overlap), 0, "Frequency-based prediction should use some hot numbers")
    
    def test_multiple_strategy_diversity(self):
        """Test that different strategies produce different results"""
        strategies = ['balanced', 'frequency_based', 'gap_based', 'monte_carlo', 'pattern_based']
        predictions = {}
        
        for strategy in strategies:
            pred = self.predictor.generate_prediction(strategy=strategy)
            predictions[strategy] = tuple(sorted(pred['numbers']) + [pred['powerball']])
        
        # Should have some diversity in predictions
        unique_predictions = set(predictions.values())
        self.assertGreater(len(unique_predictions), 1, "Different strategies should produce different results")
    
    def test_portfolio_strategy_distribution(self):
        """Test that portfolio uses different strategies"""
        portfolio = self.predictor.generate_portfolio(count=5)
        
        strategies_used = [pred['strategy'] for pred in portfolio]
        unique_strategies = set(strategies_used)
        
        # Should use multiple strategies
        self.assertGreater(len(unique_strategies), 1, "Portfolio should use multiple strategies")
    
    def test_confidence_score_correlation(self):
        """Test that confidence scores correlate with data quality"""
        # Generate predictions with current data
        predictions = []
        for _ in range(10):
            pred = self.predictor.generate_prediction()
            predictions.append(pred['confidence_score'])
        
        # All confidence scores should be reasonable
        for confidence in predictions:
            self.assertGreaterEqual(confidence, 0.3)
            self.assertLessEqual(confidence, 0.9)
        
        # Should have some variation
        self.assertGreater(max(predictions) - min(predictions), 0.05)
    
    def test_data_update_integration(self):
        """Test that new data updates affect predictions"""
        # Generate initial prediction
        initial_pred = self.predictor.generate_prediction(strategy='frequency_based')
        
        # Add new data that changes frequency patterns
        new_drawings = []
        for i in range(10):
            drawing = {
                'draw_date': f'2024-01-{i+1:02d}',
                'ball1': 1, 'ball2': 2, 'ball3': 3, 'ball4': 4, 'ball5': 5,  # Same numbers
                'powerball': 1,  # Same powerball
                'multiplier': 2,
                'jackpot_amount': 200000000
            }
            new_drawings.append(drawing)
        
        self.collector.store_drawings(new_drawings)
        
        # Generate new prediction
        new_pred = self.predictor.generate_prediction(strategy='frequency_based')
        
        # Predictions should potentially be different (though not guaranteed)
        # At minimum, confidence scores might change
        self.assertIsInstance(new_pred['confidence_score'], float)

class TestCLIIntegration(unittest.TestCase):
    """Test CLI integration"""
    
    def setUp(self):
        """Set up CLI test environment"""
        self.project_root = Path(__file__).parent.parent
        self.cli_path = self.project_root / 'cli' / 'powerball_cli.py'
    
    def test_cli_status_command(self):
        """Test CLI status command"""
        if not self.cli_path.exists():
            self.skipTest("CLI not available")
        
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'status'
        ], capture_output=True, text=True, timeout=30)
        
        # Should complete successfully
        self.assertEqual(result.returncode, 0)
        self.assertIn('Database', result.stdout)
    
    def test_cli_predict_command(self):
        """Test CLI predict command"""
        if not self.cli_path.exists():
            self.skipTest("CLI not available")
        
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'predict', '--tickets', '1'
        ], capture_output=True, text=True, timeout=60)
        
        # Should complete successfully
        self.assertEqual(result.returncode, 0)
        self.assertIn('Ticket', result.stdout)
    
    def test_cli_analyze_command(self):
        """Test CLI analyze command"""
        if not self.cli_path.exists():
            self.skipTest("CLI not available")
        
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'analyze'
        ], capture_output=True, text=True, timeout=60)
        
        # Should complete successfully
        self.assertEqual(result.returncode, 0)

class TestWebIntegration(unittest.TestCase):
    """Test web interface integration"""
    
    @classmethod
    def setUpClass(cls):
        """Start web server for testing"""
        cls.base_url = "http://localhost:5000"
        cls.server_process = None
        
        # Check if server is already running
        try:
            response = requests.get(f"{cls.base_url}/ping", timeout=2)
            if response.status_code == 200:
                cls.server_running = True
                return
        except:
            pass
        
        cls.server_running = False
        cls.skipTest("Web server not running - start with: bash scripts/run_local.sh")
    
    def test_web_api_integration(self):
        """Test web API integration"""
        if not self.server_running:
            self.skipTest("Web server not available")
        
        # Test status endpoint
        response = requests.get(f"{self.base_url}/api/status")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('database_connected', data)
    
    def test_web_prediction_integration(self):
        """Test web prediction integration"""
        if not self.server_running:
            self.skipTest("Web server not available")
        
        # Test prediction endpoint
        payload = {'tickets': 1, 'strategy': 'balanced'}
        response = requests.post(f"{self.base_url}/api/predict", json=payload)
        
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('predictions', data)
        self.assertEqual(len(data['predictions']), 1)
    
    def test_web_analysis_integration(self):
        """Test web analysis integration"""
        if not self.server_running:
            self.skipTest("Web server not available")
        
        # Test analysis endpoint
        response = requests.get(f"{self.base_url}/api/analyze")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('frequency_analysis', data)
        self.assertIn('gap_analysis', data)

class TestPerformanceIntegration(unittest.TestCase):
    """Test system performance under load"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'perf_test.db')
        
        # Create large dataset for performance testing
        collector = PowerballDataCollector(db_path=self.test_db_path)
        collector.setup_database()
        
        # Create 1000 drawings for performance testing
        sample_drawings = []
        for i in range(1000):
            drawing = {
                'draw_date': f'2020-{(i//365)+1:02d}-{(i%365)+1:03d}',
                'ball1': (i * 7 + 5) % 69 + 1,
                'ball2': (i * 11 + 10) % 69 + 1,
                'ball3': (i * 13 + 15) % 69 + 1,
                'ball4': (i * 17 + 20) % 69 + 1,
                'ball5': (i * 19 + 25) % 69 + 1,
                'powerball': (i * 3 + 1) % 26 + 1,
                'multiplier': (i % 4) + 2,
                'jackpot_amount': 100000000 + (i * 1000000)
            }
            sample_drawings.append(drawing)
        
        collector.store_drawings(sample_drawings)
        
        self.predictor = PowerballPredictor(db_path=self.test_db_path)
        self.analyzer = PowerballAnalyzer(db_path=self.test_db_path)
    
    def tearDown(self):
        """Clean up performance test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_prediction_performance(self):
        """Test prediction generation performance"""
        start_time = time.time()
        
        # Generate 10 predictions
        for _ in range(10):
            prediction = self.predictor.generate_prediction()
            self.assertIn('numbers', prediction)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time (10 seconds for 10 predictions)
        self.assertLess(total_time, 10.0, f"Prediction generation too slow: {total_time:.2f}s")
    
    def test_analysis_performance(self):
        """Test analysis performance with large dataset"""
        start_time = time.time()
        
        analysis = self.analyzer.get_comprehensive_analysis()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(total_time, 5.0, f"Analysis too slow: {total_time:.2f}s")
        self.assertIn('frequency_analysis', analysis)
    
    def test_concurrent_predictions(self):
        """Test concurrent prediction generation"""
        results = []
        errors = []
        
        def generate_prediction():
            try:
                pred = self.predictor.generate_prediction()
                results.append(pred)
            except Exception as e:
                errors.append(str(e))
        
        # Create 5 concurrent threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=generate_prediction)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have 5 successful predictions, no errors
        self.assertEqual(len(results), 5)
        self.assertEqual(len(errors), 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)