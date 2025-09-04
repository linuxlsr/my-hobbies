# PowerballAI Predictor

AI-driven Powerball number generator using statistical analysis and machine learning to optimize lottery number selection.

## ⚠️ Important Disclaimer

**This tool is for educational and entertainment purposes only.** 

- Lottery odds remain 1 in 292 million regardless of any prediction system
- No system can guarantee lottery wins
- Expected value is still negative (house edge ~50%)
- Play responsibly and within your means

## Features

- 📊 **Statistical Analysis**: Comprehensive analysis of historical Powerball data
- 🤖 **AI Predictions**: Multiple prediction strategies using machine learning
- 📈 **Pattern Recognition**: Identifies frequency patterns, gaps, and sequences
- 🎯 **Portfolio Generation**: Diversified ticket combinations for better coverage
- 💡 **Transparent Reasoning**: Clear explanations for each prediction
- 📱 **CLI Interface**: Easy-to-use command-line tools

## Quick Start

### 1. Installation

```bash
cd powerball-number-generator
pip install -r requirements.txt
```

### 2. Initialize Data

```bash
python cli/powerball_cli.py update-data
```

### 3. Generate Predictions

```bash
# Single prediction
python cli/powerball_cli.py predict

# Multiple tickets with different strategies
python cli/powerball_cli.py predict --tickets 5 --strategy portfolio

# Analyze patterns first
python cli/powerball_cli.py analyze
```

## CLI Commands

### Data Management
```bash
# Update historical data
powerball update-data --limit 200

# Check system status
powerball status
```

### Analysis
```bash
# Basic analysis
powerball analyze

# Detailed analysis with patterns
powerball analyze --format detailed

# JSON output for programmatic use
powerball analyze --format json
```

### Predictions
```bash
# Single ticket (balanced strategy)
powerball predict

# Multiple tickets with specific strategy
powerball predict --tickets 3 --strategy frequency_based

# Diversified portfolio
powerball portfolio --tickets 5

# CSV output for spreadsheets
powerball predict --tickets 10 --format csv
```

## Prediction Strategies

1. **Frequency-Based**: Selects from most frequently drawn numbers
2. **Gap-Based**: Focuses on overdue numbers that haven't appeared recently
3. **Pattern-Based**: Uses position probabilities and sequential patterns
4. **Monte Carlo**: Based on simulation results of 10,000+ scenarios
5. **Balanced**: Combines multiple approaches for optimal coverage
6. **Portfolio**: Uses all strategies for diversified ticket generation

## Example Output

```
🤖 PowerballAI Number Predictor
========================================
🎯 Generated 3 prediction(s)
📊 Average confidence: 67.3%
🔍 Data quality: 85.0%

🎫 Ticket #1 (balanced)
   Numbers: 07 23 35 42 56 + Powerball: 18
   🟡 Confidence: 68.5%
   💡 Reasoning: Balanced approach: mixed frequent and overdue numbers

🎫 Ticket #2 (frequency_based)
   Numbers: 12 19 28 41 52 + Powerball: 09
   🟢 Confidence: 72.1%
   💡 Reasoning: Selected from most frequent numbers

🎫 Ticket #3 (gap_based)
   Numbers: 03 15 31 47 59 + Powerball: 24
   🟡 Confidence: 61.3%
   💡 Reasoning: Selected overdue numbers: avg 23.4 drawings

📝 Recommendation: Moderate confidence predictions. Consider multiple tickets for better coverage.

⚠️  Remember: Lottery odds are 1 in 292 million. Play responsibly!
```

## Project Structure

```
powerball-number-generator/
├── src/
│   ├── data_collector.py    # Historical data collection
│   ├── analyzer.py          # Statistical analysis engine
│   └── predictor.py         # AI prediction algorithms
├── cli/
│   └── powerball_cli.py     # Command-line interface
├── web/                     # Web interface (coming soon)
├── data/                    # SQLite database storage
├── tests/                   # Unit tests
└── docs/                    # Documentation
```

## Data Sources

- Historical Powerball drawings (1992-present)
- Frequency analysis across multiple time periods
- Gap analysis for overdue numbers
- Sequential pattern detection
- Position-based probability distributions

## Technical Details

### Analysis Methods
- **Frequency Analysis**: Tracks number appearance rates over different time periods
- **Gap Analysis**: Calculates how long since each number was last drawn
- **Pattern Recognition**: Identifies sequential number patterns and correlations
- **Monte Carlo Simulation**: Runs thousands of probability-weighted scenarios
- **Position Analysis**: Analyzes probability distributions for each ball position

### Confidence Scoring
- Based on historical frequency patterns
- Adjusted for data quality and sample size
- Ranges from 0-85% (realistic upper bound)
- Factors in multiple statistical indicators

### Data Quality
- Validates data integrity across multiple sources
- Tracks data freshness and completeness
- Provides quality scores for predictions
- Handles missing or incomplete data gracefully

## Development Roadmap

### Phase 1: CLI Application ✅
- [x] Core data collection and analysis
- [x] Multiple prediction strategies
- [x] Command-line interface
- [x] Portfolio generation

### Phase 2: Web Interface (In Progress)
- [ ] Flask-based web dashboard
- [ ] Interactive visualizations
- [ ] Real-time analysis updates
- [ ] Prediction history tracking

### Phase 3: Production Deployment
- [ ] Docker containerization
- [ ] AWS ECS deployment
- [ ] API endpoints
- [ ] Automated data updates

## Contributing

This is an educational project demonstrating statistical analysis and machine learning concepts. Contributions welcome for:

- Additional analysis methods
- Visualization improvements
- Code optimization
- Documentation enhancements

## License

MIT License - See LICENSE file for details.

## Responsible Gaming

- Set spending limits before playing
- Never spend money you can't afford to lose
- Remember that lottery is entertainment, not investment
- Seek help if gambling becomes problematic

---

*PowerballAI Predictor - Making lottery play more intelligent, not more profitable.*
## Environment Setup

Before deploying, set up your environment variables:

1. Copy the environment template:
   ```bash
   cp env.template .env
   ```

2. Edit `.env` and set your values:
   ```bash
   export POWERBALL_SITE_NAME="your-domain.com"
   export AWS_ACCOUNT_ID="<your-aws-account-id>"
   export AWS_REGION="us-west-2"
   ```

3. Source the environment:
   ```bash
   source .env
   ```

## Deployment

The application is configured to deploy to AWS using Terraform and ECS Fargate.
Update `terraform/terraform.tfvars` with your specific configuration.
