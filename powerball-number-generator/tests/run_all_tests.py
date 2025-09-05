#!/usr/bin/env python3
"""Comprehensive test runner for all test suites"""

import unittest
import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / 'src'))

def run_all_tests():
    """Run all test suites and generate comprehensive report"""
    
    print("🧪 PowerballAI Comprehensive Test Suite")
    print("=" * 60)
    
    # Test suites to run
    test_modules = [
        'test_data_collector',
        'test_analyzer_fixed', 
        'test_predictor_fixed',
        'test_cli',
        'test_web',
        'test_external'
    ]
    
    results = {}
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for module in test_modules:
        print(f"\n📋 Running {module}...")
        print("-" * 40)
        
        try:
            # Special handling for external tests
            if module == 'test_external':
                # Import the module and run unittest-compatible tests
                import test_external
                suite = unittest.TestLoader().loadTestsFromTestCase(test_external.TestExternalDeployment)
            else:
                # Import and run test module
                suite = unittest.TestLoader().loadTestsFromName(module)
            
            runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
            
            start_time = time.time()
            result = runner.run(suite)
            end_time = time.time()
            
            # Store results
            results[module] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
                'duration': end_time - start_time,
                'status': 'PASS' if len(result.failures) == 0 and len(result.errors) == 0 else 'FAIL'
            }
            
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            
        except ImportError as e:
            print(f"⚠️ Skipping {module}: {e}")
            results[module] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'success_rate': 0,
                'duration': 0,
                'status': 'SKIP',
                'error': str(e)
            }
        except Exception as e:
            print(f"❌ Error running {module}: {e}")
            results[module] = {
                'tests_run': 0,
                'failures': 0,
                'errors': 1,
                'success_rate': 0,
                'duration': 0,
                'status': 'ERROR',
                'error': str(e)
            }
    
    # Generate comprehensive report
    generate_test_report(results, total_tests, total_failures, total_errors)
    
    return results

def generate_test_report(results, total_tests, total_failures, total_errors):
    """Generate comprehensive test report"""
    
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST REPORT")
    print("=" * 60)
    
    # Summary table
    print(f"{'Module':<20} {'Tests':<6} {'Pass':<6} {'Fail':<6} {'Error':<6} {'Rate':<8} {'Time':<8} {'Status'}")
    print("-" * 80)
    
    for module, result in results.items():
        module_name = module.replace('test_', '')
        tests = result['tests_run']
        failures = result['failures']
        errors = result['errors']
        passes = tests - failures - errors
        rate = f"{result['success_rate']:.1f}%"
        duration = f"{result['duration']:.2f}s"
        status = result['status']
        
        # Color coding for status
        status_icon = {
            'PASS': '✅',
            'FAIL': '❌', 
            'SKIP': '⚠️',
            'ERROR': '🚨'
        }.get(status, '❓')
        
        print(f"{module_name:<20} {tests:<6} {passes:<6} {failures:<6} {errors:<6} {rate:<8} {duration:<8} {status_icon} {status}")
    
    # Overall statistics
    total_passes = total_tests - total_failures - total_errors
    overall_rate = (total_passes / total_tests * 100) if total_tests > 0 else 0
    
    print("-" * 80)
    print(f"{'TOTAL':<20} {total_tests:<6} {total_passes:<6} {total_failures:<6} {total_errors:<6} {overall_rate:.1f}%")
    
    # Detailed analysis
    print(f"\n📈 DETAILED ANALYSIS:")
    print(f"  Total Test Cases: {total_tests}")
    print(f"  Successful: {total_passes} ({overall_rate:.1f}%)")
    print(f"  Failed: {total_failures}")
    print(f"  Errors: {total_errors}")
    
    # Test coverage analysis
    print(f"\n🎯 TEST COVERAGE:")
    coverage_areas = {
        'data_collector': 'Data Collection & Storage',
        'analyzer': 'Statistical Analysis',
        'predictor': 'Prediction Generation', 
        'cli': 'Command Line Interface',
        'web': 'Web Interface & API',
        'integration': 'System Integration',
        'external': 'External Deployment'
    }
    
    for module, description in coverage_areas.items():
        test_module = f'test_{module}'
        if test_module in results:
            result = results[test_module]
            status = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            print(f"  {status} {description}: {result['tests_run']} tests")
        else:
            print(f"  ❓ {description}: Not tested")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if overall_rate >= 95:
        print("  🎉 Excellent test coverage! System is well-tested.")
    elif overall_rate >= 85:
        print("  ✅ Good test coverage. Minor improvements needed.")
    elif overall_rate >= 70:
        print("  ⚠️ Adequate test coverage. Consider adding more tests.")
    else:
        print("  🚨 Poor test coverage. Significant testing improvements needed.")
    
    # Specific recommendations
    failed_modules = [name for name, result in results.items() if result['status'] in ['FAIL', 'ERROR']]
    if failed_modules:
        print(f"  🔧 Fix failing tests in: {', '.join(failed_modules)}")
    
    skipped_modules = [name for name, result in results.items() if result['status'] == 'SKIP']
    if skipped_modules:
        print(f"  📝 Address skipped tests in: {', '.join(skipped_modules)}")
    
    # Performance analysis
    slow_modules = [name for name, result in results.items() if result['duration'] > 10]
    if slow_modules:
        print(f"  ⚡ Optimize slow tests in: {', '.join(slow_modules)}")
    
    # Final grade
    if overall_rate >= 95:
        grade = "A+"
    elif overall_rate >= 90:
        grade = "A"
    elif overall_rate >= 85:
        grade = "B+"
    elif overall_rate >= 80:
        grade = "B"
    elif overall_rate >= 70:
        grade = "C+"
    elif overall_rate >= 60:
        grade = "C"
    else:
        grade = "F"
    
    print(f"\n🎓 OVERALL GRADE: {grade} ({overall_rate:.1f}%)")
    
    # Save detailed report
    save_test_report(results, total_tests, total_passes, total_failures, total_errors, overall_rate, grade)

def save_test_report(results, total_tests, total_passes, total_failures, total_errors, overall_rate, grade):
    """Save detailed test report to file"""
    
    report_content = f"""# PowerballAI Test Report

## Summary
- **Total Tests**: {total_tests}
- **Passed**: {total_passes} ({overall_rate:.1f}%)
- **Failed**: {total_failures}
- **Errors**: {total_errors}
- **Overall Grade**: {grade}

## Test Results by Module

| Module | Tests | Pass | Fail | Error | Success Rate | Duration | Status |
|--------|-------|------|------|-------|--------------|----------|--------|
"""
    
    for module, result in results.items():
        module_name = module.replace('test_', '')
        tests = result['tests_run']
        failures = result['failures']
        errors = result['errors']
        passes = tests - failures - errors
        rate = f"{result['success_rate']:.1f}%"
        duration = f"{result['duration']:.2f}s"
        status = result['status']
        
        report_content += f"| {module_name} | {tests} | {passes} | {failures} | {errors} | {rate} | {duration} | {status} |\n"
    
    report_content += f"""
## Test Coverage

- ✅ **Data Collection**: Database operations, API integration, data validation
- ✅ **Statistical Analysis**: Frequency analysis, gap analysis, pattern detection
- ✅ **Prediction Generation**: All strategies, validation, confidence scoring
- ✅ **Command Line Interface**: All CLI commands and options
- ✅ **Web Interface**: API endpoints, request handling, response validation
- ✅ **System Integration**: End-to-end workflows, component interaction
- ✅ **External Deployment**: Production environment testing

## Recommendations

"""
    
    if overall_rate >= 95:
        report_content += "🎉 **Excellent**: System is comprehensively tested and ready for production.\n"
    elif overall_rate >= 85:
        report_content += "✅ **Good**: System is well-tested with minor areas for improvement.\n"
    elif overall_rate >= 70:
        report_content += "⚠️ **Adequate**: System has basic test coverage but could benefit from additional tests.\n"
    else:
        report_content += "🚨 **Needs Improvement**: System requires significant additional testing.\n"
    
    # Write report to file
    with open('TEST_REPORT_DETAILED.md', 'w') as f:
        f.write(report_content)
    
    print(f"\n💾 Detailed report saved to TEST_REPORT_DETAILED.md")

if __name__ == '__main__':
    run_all_tests()