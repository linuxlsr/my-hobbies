#!/usr/bin/env python3
"""Test suite for PowerballAI CLI"""

import unittest
import subprocess
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

class TestPowerballCLI(unittest.TestCase):
    """Test CLI functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.cli_path = Path(__file__).parent.parent / 'cli' / 'powerball_cli.py'
        cls.test_db = Path(__file__).parent / 'test_data' / 'test.db'
        
        # Ensure test data directory exists
        cls.test_db.parent.mkdir(exist_ok=True)
        
        # Initialize test database
        result = subprocess.run([
            sys.executable, str(cls.cli_path), 'update-data'
        ], capture_output=True, text=True, cwd=cls.cli_path.parent.parent)
        
        if result.returncode != 0:
            raise Exception(f"Failed to initialize test data: {result.stderr}")
    
    def test_status_command(self):
        """Test status command"""
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'status'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('System Status', result.stdout)
        self.assertIn('Database:', result.stdout)
    
    def test_analyze_command(self):
        """Test analyze command"""
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'analyze'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Statistical Analysis', result.stdout)
        self.assertIn('Total drawings analyzed:', result.stdout)
        self.assertIn('Most Frequent White Balls:', result.stdout)
    
    def test_analyze_json_format(self):
        """Test analyze command with JSON output"""
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'analyze', '--format', 'json'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result.returncode, 0)
        
        # Validate JSON output
        try:
            data = json.loads(result.stdout)
            self.assertIn('data_summary', data)
            self.assertIn('frequency_analysis', data)
            self.assertIn('gap_analysis', data)
        except json.JSONDecodeError:
            self.fail("Output is not valid JSON")
    
    def test_predict_single_ticket(self):
        """Test single ticket prediction"""
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'predict', '--tickets', '1'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Generated 1 prediction', result.stdout)
        self.assertIn('Ticket #1', result.stdout)
        self.assertIn('Powerball:', result.stdout)
        self.assertIn('Confidence:', result.stdout)
    
    def test_predict_multiple_tickets(self):
        """Test multiple ticket predictions"""
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'predict', '--tickets', '3'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Generated 3 prediction', result.stdout)
        self.assertIn('Ticket #1', result.stdout)
        self.assertIn('Ticket #2', result.stdout)
        self.assertIn('Ticket #3', result.stdout)
    
    def test_predict_strategies(self):
        """Test different prediction strategies"""
        strategies = ['balanced', 'frequency_based', 'gap_based', 'monte_carlo', 'pattern_based']
        
        for strategy in strategies:
            with self.subTest(strategy=strategy):
                result = subprocess.run([
                    sys.executable, str(self.cli_path), 'predict', 
                    '--strategy', strategy, '--tickets', '1'
                ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
                
                self.assertEqual(result.returncode, 0, f"Strategy {strategy} failed: {result.stderr}")
                self.assertIn(f'({strategy})', result.stdout)
    
    def test_predict_csv_format(self):
        """Test CSV output format"""
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'predict', 
            '--tickets', '2', '--format', 'csv'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result.returncode, 0)
        
        lines = result.stdout.strip().split('\n')
        
        # Find CSV header line
        header_line = None
        data_start = 0
        for i, line in enumerate(lines):
            if 'Ticket,Ball1,Ball2,Ball3,Ball4,Ball5,Powerball' in line:
                header_line = line
                data_start = i + 1
                break
        
        self.assertIsNotNone(header_line, "CSV header not found")
        
        # Validate CSV data
        csv_lines = [line for line in lines[data_start:] if line.strip() and ',' in line]
        self.assertGreaterEqual(len(csv_lines), 2)  # At least 2 data rows
        
        for line in csv_lines:
            parts = line.split(',')
            self.assertEqual(len(parts), 9)  # 9 columns expected
    
    def test_portfolio_command(self):
        """Test portfolio generation"""
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'portfolio', '--tickets', '5'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Portfolio Generator', result.stdout)
        self.assertIn('Generated diversified portfolio of 5 tickets', result.stdout)
        self.assertIn('Total cost: $10', result.stdout)
    
    def test_number_validation(self):
        """Test that generated numbers are within valid ranges"""
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'predict', 
            '--tickets', '5', '--format', 'csv'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result.returncode, 0)
        
        lines = result.stdout.strip().split('\n')
        
        # Find CSV data lines
        csv_lines = []
        found_header = False
        for line in lines:
            if 'Ticket,Ball1,Ball2,Ball3,Ball4,Ball5,Powerball' in line:
                found_header = True
                continue
            if found_header and line.strip() and ',' in line:
                csv_lines.append(line)
        
        for line in csv_lines:
            parts = line.split(',')
            if len(parts) >= 7:
                # Check white balls (1-69)
                for i in range(1, 6):
                    ball = int(parts[i])
                    self.assertGreaterEqual(ball, 1)
                    self.assertLessEqual(ball, 69)
                
                # Check powerball (1-26)
                powerball = int(parts[6])
                self.assertGreaterEqual(powerball, 1)
                self.assertLessEqual(powerball, 26)
    
    def test_confidence_scores(self):
        """Test that confidence scores are reasonable"""
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'predict', 
            '--tickets', '3', '--format', 'csv'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result.returncode, 0)
        
        lines = result.stdout.strip().split('\n')
        
        # Find CSV data lines
        csv_lines = []
        found_header = False
        for line in lines:
            if 'Ticket,Ball1,Ball2,Ball3,Ball4,Ball5,Powerball' in line:
                found_header = True
                continue
            if found_header and line.strip() and ',' in line:
                csv_lines.append(line)
        
        for line in csv_lines:
            parts = line.split(',')
            if len(parts) >= 9:
                confidence = float(parts[8])  # Confidence is in column 8 (0-indexed)
                self.assertGreaterEqual(confidence, 0.0)
                self.assertLessEqual(confidence, 1.0)

class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and analysis accuracy"""
    
    def setUp(self):
        """Set up for each test"""
        self.cli_path = Path(__file__).parent.parent / 'cli' / 'powerball_cli.py'
    
    def test_data_consistency(self):
        """Test that data analysis is consistent"""
        # Run analysis twice and compare
        result1 = subprocess.run([
            sys.executable, str(self.cli_path), 'analyze', '--format', 'json'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        result2 = subprocess.run([
            sys.executable, str(self.cli_path), 'analyze', '--format', 'json'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result1.returncode, 0)
        self.assertEqual(result2.returncode, 0)
        
        data1 = json.loads(result1.stdout)
        data2 = json.loads(result2.stdout)
        
        # Data should be identical
        self.assertEqual(data1['data_summary'], data2['data_summary'])
    
    def test_prediction_uniqueness(self):
        """Test that predictions generate different combinations"""
        result = subprocess.run([
            sys.executable, str(self.cli_path), 'predict', 
            '--tickets', '10', '--format', 'csv'
        ], capture_output=True, text=True, cwd=self.cli_path.parent.parent)
        
        self.assertEqual(result.returncode, 0)
        
        combinations = set()
        lines = result.stdout.strip().split('\n')
        
        for line in lines[2:]:  # Skip header lines
            if line.strip():
                parts = line.split(',')
                if len(parts) >= 7:
                    combo = tuple(parts[1:7])  # Balls 1-5 + Powerball
                    combinations.add(combo)
        
        # Should have multiple unique combinations (allowing some duplicates)
        self.assertGreater(len(combinations), 5)

if __name__ == '__main__':
    unittest.main(verbosity=2)