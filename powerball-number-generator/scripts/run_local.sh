#!/bin/bash
set -e

echo "🚀 Starting PowerballAI locally"

# Change to project root
cd "$(dirname "$0")/.."

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Create data directory if it doesn't exist
mkdir -p data

echo "📊 Initializing database..."
python3 -c "
import sys
sys.path.insert(0, 'src')
from data_collector import PowerballDataCollector
collector = PowerballDataCollector()
collector.setup_database()
print('✅ Database initialized')
"

echo "🌐 Starting FastAPI server on http://localhost:5000"
echo "Press Ctrl+C to stop"

cd web
uvicorn app:app --host 0.0.0.0 --port 5000 --reload