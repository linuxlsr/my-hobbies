# SRE Operations Assistant Testing Framework

Comprehensive testing suite for the SRE Operations Assistant including unit tests, integration tests, and load testing.

## 🧪 Test Structure

```
testing/
├── unit/                    # Unit tests for individual components
│   └── test_mcp_functions.py
├── integration/             # End-to-end integration tests
│   └── test_slack_bot.py
├── load/                    # Load and performance tests
│   └── test_concurrent_requests.py
├── fixtures/                # Test data and mock responses
│   └── mock_responses.json
├── requirements.txt         # Testing dependencies
├── run_tests.py            # Test runner script
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r testing/requirements.txt
```

### 2. Run All Tests
```bash
python3 testing/run_tests.py --all
```

### 3. Run Specific Test Types
```bash
# Unit tests only
python3 testing/run_tests.py --unit

# Integration tests only  
python3 testing/run_tests.py --integration

# Load tests only
python3 testing/run_tests.py --load
```

## 📋 Test Categories

### Unit Tests
- **MCP Functions**: Test all 20+ MCP server functions
- **AWS Integrations**: Mock AWS service calls
- **Error Handling**: Validate error scenarios
- **Input Validation**: Test parameter validation

**Run with:**
```bash
pytest testing/unit/ -v --cov=src
```

### Integration Tests
- **End-to-End Workflows**: Complete Slack bot workflows
- **API Endpoints**: Test actual MCP server endpoints
- **Concurrent Requests**: Multi-user scenarios
- **Error Recovery**: Real-world error handling

**Run with:**
```bash
pytest testing/integration/ -v
```

### Load Tests
- **Concurrent Users**: Simulate 10+ simultaneous users
- **Performance Metrics**: Response time and throughput
- **Scaling Behavior**: Test auto-scaling triggers
- **Resource Utilization**: Monitor CPU/memory usage

**Run with:**
```bash
locust -f testing/load/test_concurrent_requests.py --host=https://sre-ops.threemoonsnetwork.net
```

## 🎯 Test Scenarios

### Vulnerability Scanning
- ✅ Single instance scan
- ✅ Multi-instance scan
- ✅ Severity filtering
- ✅ Pagination handling
- ✅ Error scenarios

### Patch Management
- ✅ Compliance checking
- ✅ Patch scheduling
- ✅ Status reporting
- ✅ Rollback scenarios

### Monitoring & Metrics
- ✅ CloudWatch metrics collection
- ✅ Custom metrics publishing
- ✅ Alert threshold testing
- ✅ Dashboard data validation

### Slack Bot Integration
- ✅ Command parsing
- ✅ Response formatting
- ✅ Async processing
- ✅ Error messaging

## 📊 Coverage Goals

- **Unit Test Coverage**: >90%
- **Integration Coverage**: All major workflows
- **Load Test Scenarios**: 10+ concurrent users
- **Error Scenarios**: All failure modes

## 🔧 Configuration

### Environment Variables
```bash
export AWS_REGION=us-west-2
export MCP_SERVER_URL=https://sre-ops.threemoonsnetwork.net
export TEST_INSTANCE_ID=i-test123
```

### Mock Configuration
Tests use `moto` library to mock AWS services:
- Inspector v2
- CloudWatch
- EC2
- Lambda
- Systems Manager

## 📈 Performance Benchmarks

### Expected Performance
- **Vulnerability Scan**: <5 seconds
- **Patch Compliance**: <3 seconds  
- **Metrics Collection**: <2 seconds
- **Health Check**: <1 second

### Load Test Targets
- **Concurrent Users**: 10-50 users
- **Request Rate**: 100+ requests/minute
- **Success Rate**: >99%
- **Response Time**: <5 seconds (95th percentile)

## 🐛 Debugging Tests

### Verbose Output
```bash
pytest testing/ -v -s --tb=long
```

### Debug Specific Test
```bash
pytest testing/unit/test_mcp_functions.py::TestAWSInspector::test_get_findings_success -v -s
```

### Coverage Report
```bash
pytest testing/unit/ --cov=src --cov-report=html
open htmlcov/index.html
```

## 🚨 Continuous Integration

### GitHub Actions (Future)
```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: python3 testing/run_tests.py --all
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Run tests before commit
pre-commit install
```

## 📝 Adding New Tests

### Unit Test Template
```python
def test_new_function():
    """Test description"""
    # Arrange
    mock_data = {...}
    
    # Act  
    result = function_under_test(mock_data)
    
    # Assert
    assert result['expected_field'] == expected_value
```

### Integration Test Template
```python
def test_new_workflow():
    """Test complete workflow"""
    # Test end-to-end scenario
    response = requests.post(endpoint, json=payload)
    assert response.status_code == 200
```

## 🏆 Test Quality Standards

- **Descriptive Names**: Clear test function names
- **AAA Pattern**: Arrange, Act, Assert
- **Independent Tests**: No test dependencies
- **Fast Execution**: Unit tests <1 second each
- **Reliable**: No flaky tests
- **Maintainable**: Easy to update and extend

---

**Built with ❤️ for reliable SRE operations**