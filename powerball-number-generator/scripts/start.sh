#!/bin/bash
set -e

echo "🚀 Starting Powerball Statistical Edge..."
echo "Working directory: $(pwd)"
echo "Python version: $(python3 --version)"

# Set working directory
cd /app

# Set Python path
export PYTHONPATH=/app/src:$PYTHONPATH

# Initialize database (non-blocking)
echo "📊 Setting up database..."
python3 -c "
import sys
sys.path.insert(0, '/app/src')
try:
    from data_collector import PowerballDataCollector
    collector = PowerballDataCollector()
    collector.setup_database()
    print('✅ Database ready')
except Exception as e:
    print(f'⚠️ Database setup issue: {e}')
    print('App will continue without initial data')
" 2>/dev/null || echo "⚠️ Database setup skipped"

# Start FastAPI application with uvicorn
echo "🌐 Starting web server on port ${PORT:-5000}..."
cd web
exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-5000} --workers 1