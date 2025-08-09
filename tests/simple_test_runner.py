#!/usr/bin/env python3
"""
Simple Security Test Runner
===========================

Simplified test runner for security regression tests.
"""

import unittest
import sys
import os
import json
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_security_tests():
    """Run all security tests and generate a simple report"""
    
    print("🔐 CLEANBOOK SECURITY TEST SUITE")
    print("=" * 50)
    print("Running security regression tests...\n")
    
    # Discover and run all tests in the tests directory
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Calculate results
    total_tests = result.testsRun
    failed_tests = len(result.failures)
    error_tests = len(result.errors)
    passed_tests = total_tests - failed_tests - error_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # Determine security status
    if failed_tests == 0 and error_tests == 0:
        security_status = "🟢 SECURE"
    elif failed_tests <= 2 and error_tests == 0:
        security_status = "🟡 WARNING"  
    else:
        security_status = "🔴 VULNERABLE"
    
    # Print summary
    print("\n" + "=" * 60)
    print("🛡️  SECURITY TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"Overall Status: {security_status}")
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"🚨 Errors: {error_tests}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    # Show failures if any
    if result.failures or result.errors:
        print(f"\n⚠️  SECURITY ISSUES DETECTED:")
        for test, error in result.failures:
            print(f"  ❌ {test}: Test failed")
        for test, error in result.errors:
            print(f"  🚨 {test}: Test error")
    
    # Generate simple report
    report = {
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": security_status,
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "errors": error_tests,
        "success_rate": success_rate
    }
    
    # Save report
    report_path = Path("security_test_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 Report saved to: {report_path.absolute()}")
    
    # Return success/failure
    return failed_tests == 0 and error_tests == 0

if __name__ == "__main__":
    success = run_security_tests()
    if success:
        print(f"\n✅ ALL SECURITY TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n🚨 SECURITY TEST FAILURES DETECTED!")
        sys.exit(1)