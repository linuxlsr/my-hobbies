#!/bin/bash
set -e

echo "🧪 Running PowerballAI Comprehensive Test Suite"
echo "================================================"

# Change to project root
cd "$(dirname "$0")/.."

# Set Python path
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Create test results directory
mkdir -p test_results

echo "📋 Available Test Suites:"
echo "  1. Unit Tests (Data Collection, Analysis, Prediction)"
echo "  2. CLI Tests"
echo "  3. Web Interface Tests"
echo "  4. Integration Tests"
echo "  5. Performance Tests"
echo "  6. External Deployment Tests"
echo ""

# Check if web server is running for web tests
WEB_SERVER_RUNNING=false
if curl -s http://localhost:5000/ping > /dev/null 2>&1; then
    WEB_SERVER_RUNNING=true
    echo "✅ Web server detected at http://localhost:5000"
else
    echo "⚠️  Web server not running - web tests will be skipped"
    echo "   Start with: bash scripts/run_local.sh"
fi

echo ""
echo "🚀 Starting test execution..."

# Run comprehensive test suite
python3 tests/run_all_tests.py

echo ""
echo "📊 Test execution complete!"
echo "📄 Check TEST_REPORT_DETAILED.md for full results"