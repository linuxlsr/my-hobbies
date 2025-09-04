#!/usr/bin/env python3
"""AI-powered number prediction engine for Powerball"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import random
from analyzer import PowerballAnalyzer

class PowerballPredictor:
    """Generates AI-driven Powerball number predictions"""
    
    def __init__(self, db_path: str = "data/powerball.db"):
        self.analyzer = PowerballAnalyzer(db_path)
        self.strategies = {
            'frequency_based': self._frequency_strategy,
            'gap_based': self._gap_strategy,
            'pattern_based': self._pattern_strategy,
            'monte_carlo': self._monte_carlo_strategy,
            'balanced': self._balanced_strategy
        }
    
    def _frequency_strategy(self, analysis: Dict) -> Tuple[List[int], int, str]:
        """Generate numbers based on frequency analysis"""
        freq_data = analysis.get('frequency_analysis', {}).get('all_time', {})
        
        if not freq_data:
            return self._random_strategy()
        
        # Get most frequent white balls
        white_freq = freq_data.get('most_frequent_white', [])
        red_freq = freq_data.get('most_frequent_red', [])
        
        if len(white_freq) < 5 or len(red_freq) < 1:
            return self._random_strategy()
        
        # Select top frequent numbers with some randomization
        white_candidates = [num for num, _ in white_freq[:15]]
        white_balls = sorted(random.sample(white_candidates, 5))
        
        red_candidates = [num for num, _ in red_freq[:8]]
        red_ball = random.choice(red_candidates)
        
        reasoning = f"Selected from most frequent numbers: white balls from top 15 frequent, red ball from top 8 frequent"
        
        return white_balls, red_ball, reasoning
    
    def _gap_strategy(self, analysis: Dict) -> Tuple[List[int], int, str]:
        """Generate numbers based on gap analysis (overdue numbers)"""
        gap_data = analysis.get('gap_analysis', {})
        
        if not gap_data:
            return self._random_strategy()
        
        # Get overdue numbers
        overdue_white = gap_data.get('overdue_white', [])
        overdue_red = gap_data.get('overdue_red', [])
        
        if len(overdue_white) < 5 or len(overdue_red) < 1:
            return self._random_strategy()
        
        # Select from most overdue numbers
        white_candidates = [num for num, _ in overdue_white[:20]]
        white_balls = sorted(random.sample(white_candidates, 5))
        
        red_candidates = [num for num, _ in overdue_red[:10]]
        red_ball = random.choice(red_candidates)
        
        reasoning = f"Selected overdue numbers: white balls overdue by avg {np.mean([gap for _, gap in overdue_white[:5]]):.1f} drawings"
        
        return white_balls, red_ball, reasoning
    
    def _pattern_strategy(self, analysis: Dict) -> Tuple[List[int], int, str]:
        """Generate numbers based on sequential patterns"""
        pattern_data = analysis.get('sequential_patterns', {})
        position_data = analysis.get('position_probabilities', {})
        
        if not position_data:
            return self._random_strategy()
        
        white_balls = []
        
        # Use position probabilities to guide selection
        for pos in range(1, 6):
            pos_key = f'position_{pos}'
            if pos_key in position_data:
                pos_probs = position_data[pos_key]['probabilities']
                # Weight by probability but add randomness
                candidates = list(pos_probs.keys())
                weights = list(pos_probs.values())
                
                # Avoid duplicates
                available = [c for c in candidates if c not in white_balls]
                if available:
                    selected = np.random.choice(available, p=[pos_probs[c]/sum(pos_probs[c] for c in available) for c in available])
                    white_balls.append(int(selected))
        
        # Fill remaining slots if needed
        while len(white_balls) < 5:
            candidate = random.randint(1, 69)
            if candidate not in white_balls:
                white_balls.append(candidate)
        
        white_balls = sorted(white_balls)
        red_ball = random.randint(1, 26)
        
        reasoning = "Selected using position-based probability distributions and pattern analysis"
        
        return white_balls, red_ball, reasoning
    
    def _monte_carlo_strategy(self, analysis: Dict) -> Tuple[List[int], int, str]:
        """Generate numbers based on Monte Carlo simulation results"""
        mc_data = analysis.get('monte_carlo_results', {})
        
        if not mc_data or not mc_data.get('most_likely_combinations'):
            return self._random_strategy()
        
        # Select from most likely combinations
        likely_combos = mc_data['most_likely_combinations']
        selected_combo = random.choice(likely_combos[:10])  # Top 10 most likely
        
        combination = selected_combo[0]
        white_balls = sorted([int(x) for x in combination[:5]])
        red_ball = int(combination[5])
        
        reasoning = f"Selected from Monte Carlo simulation of {mc_data['total_simulations']} scenarios"
        
        return white_balls, red_ball, reasoning
    
    def _balanced_strategy(self, analysis: Dict) -> Tuple[List[int], int, str]:
        """Generate numbers using a balanced approach combining multiple strategies"""
        freq_data = analysis.get('frequency_analysis', {}).get('all_time', {})
        gap_data = analysis.get('gap_analysis', {})
        
        if not freq_data or not gap_data:
            return self._random_strategy()
        
        # Mix frequent and overdue numbers
        white_freq = [num for num, _ in freq_data.get('most_frequent_white', [])[:10]]
        white_overdue = [num for num, _ in gap_data.get('overdue_white', [])[:10]]
        
        # Select 2-3 frequent, 2-3 overdue
        white_balls = []
        if white_freq:
            white_balls.extend(random.sample(white_freq, min(3, len(white_freq))))
        if white_overdue:
            remaining_slots = 5 - len(white_balls)
            available_overdue = [n for n in white_overdue if n not in white_balls]
            white_balls.extend(random.sample(available_overdue, min(remaining_slots, len(available_overdue))))
        
        # Fill remaining slots randomly
        while len(white_balls) < 5:
            candidate = random.randint(1, 69)
            if candidate not in white_balls:
                white_balls.append(candidate)
        
        white_balls = sorted(white_balls)
        
        # Balance red ball selection
        red_freq = [num for num, _ in freq_data.get('most_frequent_red', [])[:5]]
        red_overdue = [num for num, _ in gap_data.get('overdue_red', [])[:5]]
        
        red_candidates = list(set(red_freq + red_overdue))
        red_ball = random.choice(red_candidates) if red_candidates else random.randint(1, 26)
        
        reasoning = "Balanced approach: mixed frequent and overdue numbers for optimal coverage"
        
        return white_balls, red_ball, reasoning
    
    def _random_strategy(self) -> Tuple[List[int], int, str]:
        """Fallback random number generation"""
        white_balls = sorted(random.sample(range(1, 70), 5))
        red_ball = random.randint(1, 26)
        reasoning = "Random selection (fallback due to insufficient data)"
        
        return white_balls, red_ball, reasoning
    
    def generate_predictions(self, num_tickets: int = 1, strategy: str = 'balanced') -> Dict:
        """Generate number predictions using specified strategy"""
        
        # Get comprehensive analysis
        analysis = self.analyzer.get_comprehensive_analysis()
        
        if 'error' in analysis:
            return {'error': analysis['error']}
        
        # Generate predictions
        predictions = []
        
        if strategy == 'portfolio':
            # Generate diverse portfolio using different strategies
            strategies_to_use = ['frequency_based', 'gap_based', 'balanced', 'monte_carlo', 'pattern_based']
            for i in range(num_tickets):
                strategy_name = strategies_to_use[i % len(strategies_to_use)]
                white_balls, red_ball, reasoning = self.strategies[strategy_name](analysis)
                
                predictions.append({
                    'ticket_number': i + 1,
                    'numbers': white_balls,
                    'powerball': red_ball,
                    'strategy': strategy_name,
                    'reasoning': reasoning,
                    'confidence_score': self._calculate_confidence_score(white_balls, red_ball, analysis)
                })
        else:
            # Use single strategy
            if strategy not in self.strategies:
                strategy = 'balanced'
            
            for i in range(num_tickets):
                white_balls, red_ball, reasoning = self.strategies[strategy](analysis)
                
                predictions.append({
                    'ticket_number': i + 1,
                    'numbers': white_balls,
                    'powerball': red_ball,
                    'strategy': strategy,
                    'reasoning': reasoning,
                    'confidence_score': self._calculate_confidence_score(white_balls, red_ball, analysis)
                })
        
        # Calculate summary statistics
        summary = self._generate_summary(analysis, predictions)
        
        return {
            'predictions': predictions,
            'summary': summary,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_quality': {
                'total_drawings': analysis['data_summary']['total_drawings'],
                'date_range': analysis['data_summary']['date_range']
            }
        }
    
    def _calculate_confidence_score(self, white_balls: List[int], red_ball: int, analysis: Dict) -> float:
        """Calculate confidence score for prediction"""
        score = 0.5  # Base score
        
        freq_data = analysis.get('frequency_analysis', {}).get('all_time', {})
        if freq_data:
            white_freq = freq_data.get('white_ball_frequency', {})
            red_freq = freq_data.get('red_ball_frequency', {})
            
            # Boost score for frequent numbers
            total_drawings = freq_data.get('total_drawings', 1)
            for ball in white_balls:
                freq = white_freq.get(ball, 0)
                if freq > total_drawings * 0.015:  # Above average frequency
                    score += 0.05
            
            red_freq_score = red_freq.get(red_ball, 0)
            if red_freq_score > total_drawings * 0.04:  # Above average for red balls
                score += 0.1
        
        # Cap at reasonable confidence level
        return min(score, 0.85)
    
    def _generate_summary(self, analysis: Dict, predictions: List[Dict]) -> Dict:
        """Generate summary of predictions and analysis"""
        avg_confidence = np.mean([p['confidence_score'] for p in predictions])
        
        strategies_used = list(set(p['strategy'] for p in predictions))
        
        return {
            'total_predictions': len(predictions),
            'average_confidence': round(avg_confidence, 3),
            'strategies_used': strategies_used,
            'data_quality_score': min(analysis['data_summary']['total_drawings'] / 100, 1.0),
            'recommendation': self._get_recommendation(avg_confidence, analysis)
        }
    
    def _get_recommendation(self, confidence: float, analysis: Dict) -> str:
        """Generate recommendation based on analysis"""
        total_drawings = analysis['data_summary']['total_drawings']
        
        if total_drawings < 50:
            return "Limited data available. Predictions are experimental."
        elif confidence > 0.7:
            return "High confidence predictions based on strong statistical patterns."
        elif confidence > 0.6:
            return "Moderate confidence predictions. Consider multiple tickets for better coverage."
        else:
            return "Low confidence predictions. Results are primarily educational."

if __name__ == "__main__":
    predictor = PowerballPredictor()
    results = predictor.generate_predictions(num_tickets=3, strategy='portfolio')
    
    if 'error' not in results:
        print(f"Generated {len(results['predictions'])} predictions")
        for pred in results['predictions']:
            print(f"Ticket {pred['ticket_number']}: {pred['numbers']} + {pred['powerball']} (Confidence: {pred['confidence_score']:.2f})")
    else:
        print(results['error'])