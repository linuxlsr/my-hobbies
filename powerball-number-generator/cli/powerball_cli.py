#!/usr/bin/env python3
"""Command-line interface for PowerballAI Predictor"""

import click
import json
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

from data_collector import PowerballDataCollector
from analyzer import PowerballAnalyzer
from predictor import PowerballPredictor

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """PowerballAI Predictor - AI-driven lottery number generation"""
    pass

@cli.command()
@click.option('--limit', default=200, help='Number of recent drawings to fetch')
def update_data(limit):
    """Update historical Powerball data"""
    click.echo("🎱 PowerballAI Data Updater")
    click.echo("=" * 40)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    collector = PowerballDataCollector()
    collector.setup_database()
    
    click.echo(f"Fetching last {limit} drawings...")
    collector.update_data()
    
    summary = collector.get_data_summary()
    click.echo(f"✅ Database updated: {summary['total_drawings']} total drawings")
    click.echo(f"📅 Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")

@cli.command()
@click.option('--format', default='summary', type=click.Choice(['summary', 'detailed', 'json']), 
              help='Output format')
def analyze(format):
    """Analyze historical patterns in Powerball data"""
    analyzer = PowerballAnalyzer()
    analysis = analyzer.get_comprehensive_analysis()
    
    if 'error' in analysis:
        if format == 'json':
            click.echo(json.dumps({'error': analysis['error']}))
        else:
            click.echo(f"❌ Error: {analysis['error']}")
        return
    
    if format == 'json':
        # Convert tuples to strings for JSON serialization
        def convert_for_json(obj):
            if isinstance(obj, dict):
                return {str(k): convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            elif isinstance(obj, tuple):
                return list(obj)
            else:
                return obj
        
        json_analysis = convert_for_json(analysis)
        click.echo(json.dumps(json_analysis, indent=2, default=str))
        return
    
    # Only show headers for non-JSON output
    click.echo("🔍 PowerballAI Statistical Analysis")
    click.echo("=" * 40)
    
    # Summary format
    data_summary = analysis['data_summary']
    click.echo(f"📊 Total drawings analyzed: {data_summary['total_drawings']}")
    click.echo(f"📅 Date range: {data_summary['date_range']['earliest']} to {data_summary['date_range']['latest']}")
    click.echo()
    
    # Frequency analysis
    freq_data = analysis.get('frequency_analysis', {}).get('all_time', {})
    if freq_data:
        click.echo("🔥 Most Frequent White Balls:")
        for num, count in freq_data['most_frequent_white'][:10]:
            click.echo(f"   {num}: {count} times")
        
        click.echo("\n🔴 Most Frequent Red Balls:")
        for num, count in freq_data['most_frequent_red'][:5]:
            click.echo(f"   {num}: {count} times")
    
    # Gap analysis
    gap_data = analysis.get('gap_analysis', {})
    if gap_data:
        click.echo("\n⏰ Most Overdue White Balls:")
        for num, gap in gap_data['overdue_white'][:10]:
            click.echo(f"   {num}: {gap} drawings ago")
        
        click.echo("\n🔴 Most Overdue Red Balls:")
        for num, gap in gap_data['overdue_red'][:5]:
            click.echo(f"   {num}: {gap} drawings ago")
    
    if format == 'detailed':
        # Sequential patterns
        seq_data = analysis.get('sequential_patterns', {})
        if seq_data and seq_data.get('most_common_sequences'):
            click.echo("\n🔢 Sequential Patterns Found:")
            for pattern, count in seq_data['most_common_sequences'][:5]:
                click.echo(f"   {pattern}: {count} times")

@cli.command()
@click.option('--tickets', default=1, help='Number of tickets to generate')
@click.option('--strategy', default='balanced', 
              type=click.Choice(['frequency_based', 'gap_based', 'pattern_based', 'monte_carlo', 'balanced', 'portfolio']),
              help='Prediction strategy to use')
@click.option('--format', default='standard', type=click.Choice(['standard', 'json', 'csv']),
              help='Output format')
def predict(tickets, strategy, format):
    """Generate AI-powered number predictions"""
    click.echo("🤖 PowerballAI Number Predictor")
    click.echo("=" * 40)
    
    predictor = PowerballPredictor()
    results = predictor.generate_predictions(num_tickets=tickets, strategy=strategy)
    
    if 'error' in results:
        click.echo(f"❌ Error: {results['error']}")
        return
    
    if format == 'json':
        click.echo(json.dumps(results, indent=2, default=str))
        return
    
    if format == 'csv':
        click.echo("Ticket,Ball1,Ball2,Ball3,Ball4,Ball5,Powerball,Strategy,Confidence")
        for pred in results['predictions']:
            balls = pred['numbers']
            click.echo(f"{pred['ticket_number']},{balls[0]},{balls[1]},{balls[2]},{balls[3]},{balls[4]},{pred['powerball']},{pred['strategy']},{pred['confidence_score']:.3f}")
        return
    
    # Standard format
    click.echo(f"🎯 Generated {len(results['predictions'])} prediction(s)")
    click.echo(f"📊 Average confidence: {results['summary']['average_confidence']:.1%}")
    click.echo(f"🔍 Data quality: {results['summary']['data_quality_score']:.1%}")
    click.echo()
    
    for pred in results['predictions']:
        confidence_emoji = "🟢" if pred['confidence_score'] > 0.7 else "🟡" if pred['confidence_score'] > 0.6 else "🔴"
        
        click.echo(f"🎫 Ticket #{pred['ticket_number']} ({pred['strategy']})")
        click.echo(f"   Numbers: {' '.join(f'{n:2d}' for n in pred['numbers'])} + Powerball: {pred['powerball']:2d}")
        click.echo(f"   {confidence_emoji} Confidence: {pred['confidence_score']:.1%}")
        click.echo(f"   💡 Reasoning: {pred['reasoning']}")
        click.echo()
    
    click.echo(f"📝 Recommendation: {results['summary']['recommendation']}")
    click.echo()
    click.echo("⚠️  Remember: Lottery odds are 1 in 292 million. Play responsibly!")

@cli.command()
def status():
    """Show system status and data summary"""
    click.echo("📊 PowerballAI System Status")
    click.echo("=" * 40)
    
    # Check database
    db_path = "data/powerball.db"
    if os.path.exists(db_path):
        collector = PowerballDataCollector()
        summary = collector.get_data_summary()
        
        click.echo(f"✅ Database: Connected")
        click.echo(f"📊 Total drawings: {summary['total_drawings']}")
        click.echo(f"📅 Date range: {summary['date_range']['earliest']} to {summary['date_range']['latest']}")
        
        if summary['total_drawings'] < 50:
            click.echo("⚠️  Warning: Limited data available. Run 'powerball update-data' first.")
        elif summary['total_drawings'] < 200:
            click.echo("🟡 Data quality: Moderate (consider updating data)")
        else:
            click.echo("🟢 Data quality: Good")
    else:
        click.echo("❌ Database: Not found")
        click.echo("💡 Run 'powerball update-data' to initialize")
    
    click.echo()
    click.echo("🔧 Available commands:")
    click.echo("   update-data  - Fetch latest Powerball drawings")
    click.echo("   analyze      - Analyze historical patterns")
    click.echo("   predict      - Generate number predictions")
    click.echo("   status       - Show this status")

@cli.command()
@click.option('--tickets', default=5, help='Number of tickets in portfolio')
def portfolio(tickets):
    """Generate a diversified portfolio of predictions"""
    click.echo("📈 PowerballAI Portfolio Generator")
    click.echo("=" * 40)
    
    predictor = PowerballPredictor()
    results = predictor.generate_predictions(num_tickets=tickets, strategy='portfolio')
    
    if 'error' in results:
        click.echo(f"❌ Error: {results['error']}")
        return
    
    click.echo(f"🎯 Generated diversified portfolio of {len(results['predictions'])} tickets")
    click.echo(f"📊 Average confidence: {results['summary']['average_confidence']:.1%}")
    click.echo(f"🎲 Strategies used: {', '.join(results['summary']['strategies_used'])}")
    click.echo()
    
    total_cost = len(results['predictions']) * 2  # $2 per ticket
    click.echo(f"💰 Total cost: ${total_cost}")
    click.echo()
    
    for pred in results['predictions']:
        strategy_emoji = {
            'frequency_based': '🔥',
            'gap_based': '⏰',
            'pattern_based': '🔢',
            'monte_carlo': '🎲',
            'balanced': '⚖️'
        }.get(pred['strategy'], '🎯')
        
        click.echo(f"{strategy_emoji} Ticket #{pred['ticket_number']} - {pred['strategy'].replace('_', ' ').title()}")
        click.echo(f"   {' '.join(f'{n:2d}' for n in pred['numbers'])} + {pred['powerball']:2d} (Confidence: {pred['confidence_score']:.1%})")
    
    click.echo()
    click.echo(f"📝 {results['summary']['recommendation']}")

if __name__ == '__main__':
    cli()