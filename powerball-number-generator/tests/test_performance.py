#!/usr/bin/env python3
"""Performance and load tests"""

import unittest
import time
import threading
import tempfile
import os
import sys
from pathlib import Path
import statistics

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from data_collector import PowerballDataCollector
from analyzer import PowerballAnalyzer
from predictor import PowerballPredictor

class TestPerformance(unittest.TestCase):
    """Performance benchmarking tests"""
    
    def setUp(self):
        """Set up performance test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'perf_test.db')
        
        # Create large dataset for performance testing
        collector = PowerballDataCollector(db_path=self.test_db_path)
        collector.setup_database()
        
        # Create realistic dataset size (3000+ drawings)
        sample_drawings = []
        for i in range(3000):
            drawing = {
                'draw_date': f'{2000 + (i//156):04d}-{((i%156)//13)+1:02d}-{((i%13)*2)+1:02d}',
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
        
        self.collector = collector
        self.analyzer = PowerballAnalyzer(db_path=self.test_db_path)
        self.predictor = PowerballPredictor(db_path=self.test_db_path)
    
    def tearDown(self):
        """Clean up performance test environment"""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_query_performance(self):
        """Test database query performance"""
        times = []
        
        for _ in range(10):
            start_time = time.time()
            df = self.collector.get_historical_data(limit=1000)
            end_time = time.time()
            
            times.append(end_time - start_time)
            self.assertFalse(df.empty)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        print(f"Database query - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
        
        # Should complete within reasonable time
        self.assertLess(avg_time, 1.0, f"Database queries too slow: {avg_time:.3f}s average")
        self.assertLess(max_time, 2.0, f"Slowest query too slow: {max_time:.3f}s")
    
    def test_frequency_analysis_performance(self):
        """Test frequency analysis performance"""
        times = []
        
        for _ in range(5):
            start_time = time.time()
            analysis = self.analyzer.get_frequency_analysis()
            end_time = time.time()
            
            times.append(end_time - start_time)
            self.assertIn('white_balls', analysis)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        print(f"Frequency analysis - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
        
        self.assertLess(avg_time, 2.0, f"Frequency analysis too slow: {avg_time:.3f}s average")
    
    def test_comprehensive_analysis_performance(self):
        """Test comprehensive analysis performance"""
        start_time = time.time()
        analysis = self.analyzer.get_comprehensive_analysis()
        end_time = time.time()
        
        duration = end_time - start_time
        
        print(f"Comprehensive analysis: {duration:.3f}s")
        
        self.assertIn('frequency_analysis', analysis)
        self.assertIn('gap_analysis', analysis)
        self.assertIn('pattern_analysis', analysis)
        
        # Should complete within reasonable time even with large dataset
        self.assertLess(duration, 5.0, f"Comprehensive analysis too slow: {duration:.3f}s")
    
    def test_prediction_generation_performance(self):
        """Test prediction generation performance"""
        strategies = ['balanced', 'frequency_based', 'gap_based', 'monte_carlo', 'pattern_based']
        
        for strategy in strategies:
            times = []
            
            for _ in range(5):
                start_time = time.time()
                prediction = self.predictor.generate_prediction(strategy=strategy)
                end_time = time.time()
                
                times.append(end_time - start_time)
                self.assertIn('numbers', prediction)
            
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            print(f"{strategy} prediction - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
            
            # Each prediction should be fast
            self.assertLess(avg_time, 3.0, f"{strategy} prediction too slow: {avg_time:.3f}s average")
    
    def test_multiple_predictions_performance(self):
        """Test multiple predictions performance"""
        start_time = time.time()
        predictions = self.predictor.generate_multiple_predictions(count=10)
        end_time = time.time()
        
        duration = end_time - start_time
        per_prediction = duration / 10
        
        print(f"10 predictions: {duration:.3f}s total, {per_prediction:.3f}s per prediction")
        
        self.assertEqual(len(predictions), 10)
        self.assertLess(duration, 15.0, f"Multiple predictions too slow: {duration:.3f}s")
        self.assertLess(per_prediction, 2.0, f"Per prediction too slow: {per_prediction:.3f}s")
    
    def test_portfolio_generation_performance(self):
        """Test portfolio generation performance"""
        start_time = time.time()
        portfolio = self.predictor.generate_portfolio(count=5)
        end_time = time.time()
        
        duration = end_time - start_time
        
        print(f"Portfolio generation (5 tickets): {duration:.3f}s")
        
        self.assertEqual(len(portfolio), 5)
        self.assertLess(duration, 10.0, f"Portfolio generation too slow: {duration:.3f}s")
    
    def test_concurrent_predictions(self):
        """Test concurrent prediction performance"""
        results = []
        errors = []
        
        def generate_prediction():
            try:
                start_time = time.time()
                pred = self.predictor.generate_prediction()
                end_time = time.time()
                results.append({
                    'prediction': pred,
                    'duration': end_time - start_time
                })
            except Exception as e:
                errors.append(str(e))
        
        # Test with 5 concurrent threads
        threads = []
        start_time = time.time()
        
        for _ in range(5):
            thread = threading.Thread(target=generate_prediction)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        print(f"5 concurrent predictions: {total_duration:.3f}s total")
        
        # Should have 5 successful predictions
        self.assertEqual(len(results), 5)
        self.assertEqual(len(errors), 0)
        
        # Concurrent execution should be faster than sequential
        individual_times = [r['duration'] for r in results]
        avg_individual = statistics.mean(individual_times)
        
        print(f"Average individual time: {avg_individual:.3f}s")
        
        # Total time should be less than sum of individual times (parallelism benefit)
        self.assertLess(total_duration, sum(individual_times) * 0.8)
    
    def test_memory_usage_stability(self):
        """Test memory usage doesn't grow excessively"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate many predictions to test memory stability
        for i in range(50):
            prediction = self.predictor.generate_prediction()
            self.assertIn('numbers', prediction)
            
            # Check memory every 10 iterations
            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_growth = current_memory - initial_memory
                
                # Memory growth should be reasonable (less than 100MB)
                self.assertLess(memory_growth, 100, 
                    f"Excessive memory growth: {memory_growth:.1f}MB after {i+1} predictions")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_growth = final_memory - initial_memory
        
        print(f"Memory usage - Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB, Growth: {total_growth:.1f}MB")
        
        # Total memory growth should be reasonable
        self.assertLess(total_growth, 50, f"Excessive total memory growth: {total_growth:.1f}MB")

class TestScalability(unittest.TestCase):
    """Test system scalability with varying data sizes"""
    
    def test_scalability_with_data_size(self):
        """Test performance scaling with different data sizes"""
        data_sizes = [100, 500, 1000, 2000]
        results = {}
        
        for size in data_sizes:
            temp_dir = tempfile.mkdtemp()
            test_db_path = os.path.join(temp_dir, f'scale_test_{size}.db')
            
            try:
                # Create dataset of specified size
                collector = PowerballDataCollector(db_path=test_db_path)
                collector.setup_database()
                
                sample_drawings = []
                for i in range(size):
                    drawing = {
                        'draw_date': f'{2000 + (i//156):04d}-{((i%156)//13)+1:02d}-{((i%13)*2)+1:02d}',
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
                
                # Test prediction performance
                predictor = PowerballPredictor(db_path=test_db_path)
                
                start_time = time.time()
                prediction = predictor.generate_prediction()
                end_time = time.time()
                
                duration = end_time - start_time
                results[size] = duration
                
                print(f"Data size {size}: {duration:.3f}s")
                
                self.assertIn('numbers', prediction)
                
            finally:
                # Cleanup
                if os.path.exists(test_db_path):
                    os.remove(test_db_path)
                os.rmdir(temp_dir)
        
        # Analyze scaling behavior
        print(f"Scalability results: {results}")
        
        # Performance shouldn't degrade dramatically with more data
        max_time = max(results.values())
        min_time = min(results.values())
        
        # Should scale reasonably (less than 10x slowdown for 20x data)
        self.assertLess(max_time / min_time, 10, 
            f"Poor scalability: {max_time/min_time:.1f}x slowdown")

if __name__ == '__main__':
    unittest.main(verbosity=2)