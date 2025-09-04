#!/usr/bin/env python3
"""Statistical analysis engine for Powerball data"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import Counter
import sqlite3
from datetime import datetime, timedelta

class PowerballAnalyzer:
    """Analyzes Powerball historical data for patterns and predictions"""
    
    def __init__(self, db_path: str = "data/powerball.db"):
        self.db_path = db_path
        self.data = None
        self.load_data()
    
    def load_data(self):
        """Load historical data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            self.data = pd.read_sql_query(
                "SELECT * FROM drawings ORDER BY draw_date DESC", 
                conn
            )
            conn.close()
            
            if not self.data.empty:
                self.data['draw_date'] = pd.to_datetime(self.data['draw_date'])
        except Exception as e:
            print(f"Error loading data: {e}")
            self.data = pd.DataFrame()
    
    def analyze_frequency_patterns(self, lookback_periods: List = [30, 90, 365, 'all']) -> Dict:
        """Analyze frequency patterns for different time periods"""
        if self.data.empty:
            return {}
        
        results = {}
        
        for period in lookback_periods:
            if period == 'all':
                subset = self.data
                period_name = 'all_time'
            else:
                cutoff_date = datetime.now() - timedelta(days=period)
                subset = self.data[self.data['draw_date'] >= cutoff_date]
                period_name = f'last_{period}_days'
            
            if subset.empty:
                continue
                
            # Analyze white balls (1-69)
            white_balls = []
            for col in ['ball1', 'ball2', 'ball3', 'ball4', 'ball5']:
                white_balls.extend(subset[col].tolist())
            
            white_freq = Counter(white_balls)
            
            # Analyze red balls (1-26)
            red_freq = Counter(subset['powerball'].tolist())
            
            results[period_name] = {
                'white_ball_frequency': dict(white_freq),
                'red_ball_frequency': dict(red_freq),
                'total_drawings': len(subset),
                'most_frequent_white': white_freq.most_common(10),
                'least_frequent_white': white_freq.most_common()[-10:],
                'most_frequent_red': red_freq.most_common(5),
                'least_frequent_red': red_freq.most_common()[-5:]
            }
        
        return results
    
    def calculate_gaps(self) -> Dict:
        """Calculate how long since each number was last drawn"""
        if self.data.empty:
            return {}
        
        # Sort by date descending (most recent first) for gap calculation
        sorted_data = self.data.sort_values('draw_date', ascending=False)
        
        white_gaps = {}
        red_gaps = {}
        
        # Initialize all numbers with max gap
        for i in range(1, 70):
            white_gaps[i] = len(sorted_data)
        for i in range(1, 27):
            red_gaps[i] = len(sorted_data)
        
        # Calculate gaps from most recent drawing backwards
        for drawings_ago, (idx, row) in enumerate(sorted_data.iterrows()):
            # Update white ball gaps (only update if not already found)
            for col in ['ball1', 'ball2', 'ball3', 'ball4', 'ball5']:
                number = row[col]
                if white_gaps[number] == len(sorted_data):  # Not yet found
                    white_gaps[number] = drawings_ago
            
            # Update red ball gap
            red_number = row['powerball']
            if red_gaps[red_number] == len(sorted_data):  # Not yet found
                red_gaps[red_number] = drawings_ago
        
        return {
            'white_ball_gaps': white_gaps,
            'red_ball_gaps': red_gaps,
            'overdue_white': sorted(white_gaps.items(), key=lambda x: x[1], reverse=True)[:10],
            'overdue_red': sorted(red_gaps.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def detect_sequential_patterns(self, pattern_length: int = 3) -> Dict:
        """Detect sequential number patterns"""
        if self.data.empty:
            return {}
        
        patterns = []
        
        for _, row in self.data.iterrows():
            balls = sorted([row['ball1'], row['ball2'], row['ball3'], row['ball4'], row['ball5']])
            
            # Check for consecutive sequences
            for i in range(len(balls) - pattern_length + 1):
                sequence = balls[i:i + pattern_length]
                if all(sequence[j] + 1 == sequence[j + 1] for j in range(len(sequence) - 1)):
                    patterns.append(tuple(sequence))
        
        pattern_freq = Counter(patterns)
        
        return {
            'sequential_patterns': dict(pattern_freq),
            'most_common_sequences': pattern_freq.most_common(10),
            'total_sequences_found': len(patterns)
        }
    
    def calculate_position_probabilities(self) -> Dict:
        """Calculate probability distributions for each ball position"""
        if self.data.empty:
            return {}
        
        position_stats = {}
        
        for pos, col in enumerate(['ball1', 'ball2', 'ball3', 'ball4', 'ball5'], 1):
            values = self.data[col].tolist()
            freq = Counter(values)
            total = len(values)
            
            probabilities = {num: count/total for num, count in freq.items()}
            
            position_stats[f'position_{pos}'] = {
                'frequencies': dict(freq),
                'probabilities': probabilities,
                'mean': np.mean(values),
                'std': np.std(values),
                'most_likely': max(probabilities.items(), key=lambda x: x[1])
            }
        
        return position_stats
    
    def generate_monte_carlo_scenarios(self, num_simulations: int = 10000) -> Dict:
        """Generate Monte Carlo simulation scenarios"""
        if self.data.empty:
            return {}
        
        # Get frequency distributions
        freq_analysis = self.analyze_frequency_patterns(['all'])
        if not freq_analysis:
            return {}
        
        white_freq = freq_analysis['all_time']['white_ball_frequency']
        red_freq = freq_analysis['all_time']['red_ball_frequency']
        
        # Create weighted probability distributions
        white_numbers = list(range(1, 70))
        white_weights = [white_freq.get(num, 1) for num in white_numbers]
        
        red_numbers = list(range(1, 27))
        red_weights = [red_freq.get(num, 1) for num in red_numbers]
        
        # Normalize weights
        white_weights = np.array(white_weights) / sum(white_weights)
        red_weights = np.array(red_weights) / sum(red_weights)
        
        simulated_combinations = []
        
        for _ in range(num_simulations):
            # Generate 5 white balls without replacement
            white_balls = sorted([int(x) for x in np.random.choice(
                white_numbers, 
                size=5, 
                replace=False, 
                p=white_weights
            )])
            
            # Generate 1 red ball
            red_ball = int(np.random.choice(red_numbers, p=red_weights))
            
            combination = tuple(white_balls + [red_ball])
            simulated_combinations.append(combination)
        
        # Analyze simulation results
        combo_freq = Counter(simulated_combinations)
        
        return {
            'total_simulations': num_simulations,
            'unique_combinations': len(combo_freq),
            'most_likely_combinations': combo_freq.most_common(20),
            'simulation_summary': {
                'avg_white_ball': np.mean([np.mean(combo[:5]) for combo in simulated_combinations]),
                'avg_red_ball': np.mean([combo[5] for combo in simulated_combinations])
            }
        }
    
    def create_exclusive_groups(self) -> Dict:
        """Create mutually exclusive frequent vs overdue groups"""
        if self.data.empty:
            return {}
        
        freq_analysis = self.analyze_frequency_patterns(['all'])
        gap_analysis = self.calculate_gaps()
        
        if not freq_analysis or not gap_analysis:
            return {}
        
        # Get frequency data
        white_freq = freq_analysis['all_time']['most_frequent_white']
        red_freq = freq_analysis['all_time']['most_frequent_red']
        
        # Get gap data
        white_overdue = gap_analysis['overdue_white']
        red_overdue = gap_analysis['overdue_red']
        
        # Create exclusive groups by removing overlaps
        frequent_white = [num for num, count in white_freq[:15]]  # Top 15 frequent
        overdue_white = [num for num, gap in white_overdue if num not in frequent_white][:10]
        
        frequent_red = [num for num, count in red_freq[:8]]  # Top 8 frequent
        overdue_red = [num for num, gap in red_overdue if num not in frequent_red][:5]
        
        return {
            'exclusive_frequent_white': frequent_white[:10],
            'exclusive_overdue_white': overdue_white[:10],
            'exclusive_frequent_red': frequent_red[:5],
            'exclusive_overdue_red': overdue_red[:5]
        }
    
    def get_comprehensive_analysis(self) -> Dict:
        """Get comprehensive analysis of all patterns"""
        if self.data.empty:
            return {'error': 'No data available'}
        
        # Get exclusive groups
        exclusive_groups = self.create_exclusive_groups()
        
        return {
            'data_summary': {
                'total_drawings': len(self.data),
                'date_range': {
                    'earliest': self.data['draw_date'].min().strftime('%Y-%m-%d'),
                    'latest': self.data['draw_date'].max().strftime('%Y-%m-%d')
                }
            },
            'frequency_analysis': self.analyze_frequency_patterns(),
            'gap_analysis': self.calculate_gaps(),
            'exclusive_groups': exclusive_groups,
            'sequential_patterns': self.detect_sequential_patterns(),
            'position_probabilities': self.calculate_position_probabilities(),
            'monte_carlo_results': self.generate_monte_carlo_scenarios(1000)
        }

if __name__ == "__main__":
    analyzer = PowerballAnalyzer()
    analysis = analyzer.get_comprehensive_analysis()
    
    if 'error' not in analysis:
        print(f"Analyzed {analysis['data_summary']['total_drawings']} drawings")
        print(f"Date range: {analysis['data_summary']['date_range']['earliest']} to {analysis['data_summary']['date_range']['latest']}")
    else:
        print(analysis['error'])