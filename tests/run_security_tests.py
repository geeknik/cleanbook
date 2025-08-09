#!/usr/bin/env python3
"""
Comprehensive Security Test Runner
=================================

Main test runner for all security regression tests. This script runs the complete
test suite to verify that all security patches and protections are working correctly.

Usage:
    python3 tests/run_security_tests.py                    # Run all tests
    python3 tests/run_security_tests.py --verbose          # Verbose output
    python3 tests/run_security_tests.py --category path    # Run specific category
    python3 tests/run_security_tests.py --quick            # Run quick/essential tests only
    python3 tests/run_security_tests.py --report           # Generate detailed report
"""

import unittest
import sys
import os
import argparse
import json
import time
from pathlib import Path
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import all test modules
from tests.test_path_traversal_protection import TestPathTraversalProtection
from tests.test_toctou_protection import TestTOCTOUProtection
from tests.test_size_threshold_validation import TestSizeThresholdValidation
from tests.test_symlink_security import TestSymlinkSecurity
from tests.test_secure_temp_files import TestSecureTempFiles


class SecurityTestResult(unittest.TestResult):
    """Custom test result class that captures detailed security test information"""
    
    def __init__(self):
        super().__init__()
        self.security_results = {
            'passed': [],
            'failed': [],
            'errors': [],
            'skipped': [],
            'categories': {}
        }
        self.start_time = None
        self.end_time = None
    
    def startTest(self, test):
        super().startTest(test)
        if self.start_time is None:
            self.start_time = time.time()
    
    def stopTest(self, test):
        super().stopTest(test)
        self.end_time = time.time()
    
    def addSuccess(self, test):
        super().addSuccess(test)
        test_info = self._get_test_info(test)
        self.security_results['passed'].append(test_info)
        self._add_to_category(test_info)
    
    def addError(self, test, err):
        super().addError(test, err)
        test_info = self._get_test_info(test)
        test_info['error'] = str(err[1])
        self.security_results['errors'].append(test_info)
        self._add_to_category(test_info)
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        test_info = self._get_test_info(test)
        test_info['failure'] = str(err[1])
        self.security_results['failed'].append(test_info)
        self._add_to_category(test_info)
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        test_info = self._get_test_info(test)
        test_info['skip_reason'] = reason
        self.security_results['skipped'].append(test_info)
        self._add_to_category(test_info)
    
    def _get_test_info(self, test):
        """Extract information about a test"""
        test_method = test._testMethodName
        test_class = test.__class__.__name__
        test_module = test.__class__.__module__
        
        # Determine security category
        category = 'unknown'
        if 'path_traversal' in test_module:
            category = 'path_traversal'
        elif 'toctou' in test_module:
            category = 'race_conditions'
        elif 'size_threshold' in test_module:
            category = 'input_validation'
        elif 'symlink' in test_module:
            category = 'symlink_security'
        elif 'temp_files' in test_module:
            category = 'temp_file_security'
        
        return {
            'method': test_method,
            'class': test_class,
            'module': test_module,
            'category': category,
            'full_name': f"{test_class}.{test_method}"
        }
    
    def _add_to_category(self, test_info):
        """Add test to category tracking"""
        category = test_info['category']
        if category not in self.security_results['categories']:
            self.security_results['categories'][category] = {
                'passed': 0, 'failed': 0, 'errors': 0, 'skipped': 0, 'total': 0
            }
        
        self.security_results['categories'][category]['total'] += 1
        
        if test_info in self.security_results['passed']:
            self.security_results['categories'][category]['passed'] += 1
        elif test_info in self.security_results['failed']:
            self.security_results['categories'][category]['failed'] += 1
        elif test_info in self.security_results['errors']:
            self.security_results['categories'][category]['errors'] += 1
        elif test_info in self.security_results['skipped']:
            self.security_results['categories'][category]['skipped'] += 1


class SecurityTestRunner:
    """Main security test runner"""
    
    def __init__(self):
        self.all_test_classes = [
            TestPathTraversalProtection,
            TestTOCTOUProtection,
            TestSizeThresholdValidation,
            TestSymlinkSecurity,
            TestSecureTempFiles
        ]
    
    def create_test_suite(self, category_filter=None, quick_mode=False):
        """Create test suite with optional filtering"""
        suite = unittest.TestSuite()
        
        for test_class in self.all_test_classes:
            # Category filtering
            if category_filter:
                class_name = test_class.__name__.lower()
                if category_filter.lower() not in class_name:
                    continue
            
            # Load tests from class
            loader = unittest.TestLoader()
            class_tests = loader.loadTestsFromTestCase(test_class)
            
            if quick_mode:
                # In quick mode, only run essential tests
                essential_tests = unittest.TestSuite()
                for test in class_tests:
                    test_name = test._testMethodName
                    # Include tests that are marked as essential or basic security checks
                    if any(keyword in test_name for keyword in [
                        'blocks_system', 'rejects', 'validation', 'protection', 
                        'detection', 'security', 'basic', 'essential'
                    ]):
                        essential_tests.addTest(test)
                suite.addTest(essential_tests)
            else:
                suite.addTest(class_tests)
        
        return suite
    
    def run_tests(self, suite, verbose=False):
        """Run the test suite with custom result tracking"""
        # Capture output
        output_stream = StringIO()
        
        # Create custom test result
        result = SecurityTestResult()
        
        # Create test runner
        runner = unittest.TextTestRunner(
            stream=output_stream,
            verbosity=2 if verbose else 1
        )
        
        # Run tests
        print("🔐 CLEANBOOK SECURITY TEST SUITE")
        print("=" * 50)
        print("Running comprehensive security regression tests...")
        print()
        
        final_result = runner.run(suite)
        
        # Get output
        test_output = output_stream.getvalue()
        
        return result, test_output
    
    def generate_security_report(self, result, output, save_to_file=True):
        """Generate comprehensive security test report"""
        total_tests = (len(result.security_results['passed']) + 
                      len(result.security_results['failed']) + 
                      len(result.security_results['errors']) + 
                      len(result.security_results['skipped']))
        
        passed_tests = len(result.security_results['passed'])
        failed_tests = len(result.security_results['failed'])
        error_tests = len(result.security_results['errors'])
        skipped_tests = len(result.security_results['skipped'])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall security status
        if failed_tests == 0 and error_tests == 0:
            security_status = "🟢 SECURE"
            status_color = "green"
        elif failed_tests <= 2 and error_tests == 0:
            security_status = "🟡 WARNING"
            status_color = "yellow"
        else:
            security_status = "🔴 VULNERABLE"
            status_color = "red"
        
        # Create detailed report
        report = {
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": security_status,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "skipped": skipped_tests,
                "success_rate": round(success_rate, 2)
            },
            "categories": result.security_results['categories'],
            "failed_tests": [
                {
                    "test": test['full_name'],
                    "category": test['category'],
                    "failure": test.get('failure', 'Unknown failure')
                }
                for test in result.security_results['failed']
            ],
            "error_tests": [
                {
                    "test": test['full_name'],
                    "category": test['category'],
                    "error": test.get('error', 'Unknown error')
                }
                for test in result.security_results['errors']
            ],
            "execution_time": result.end_time - result.start_time if result.start_time else 0
        }
        
        # Print summary to console
        print("\n" + "=" * 60)
        print("🛡️  SECURITY TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Overall Status: {security_status}")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🚨 Errors: {error_tests}")
        print(f"⏭️  Skipped: {skipped_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Execution Time: {report['execution_time']:.2f}s")
        
        # Category breakdown
        if result.security_results['categories']:
            print(f"\n📋 SECURITY CATEGORY BREAKDOWN:")
            for category, stats in result.security_results['categories'].items():
                category_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"  {category.replace('_', ' ').title()}: {stats['passed']}/{stats['total']} ({category_rate:.1f}%)")
        
        # Failed tests details
        if result.security_results['failed'] or result.security_results['errors']:
            print(f"\n⚠️  SECURITY ISSUES DETECTED:")
            for test in result.security_results['failed']:
                print(f"  ❌ {test['full_name']}: {test.get('failure', 'Test failed')}")
            for test in result.security_results['errors']:
                print(f"  🚨 {test['full_name']}: {test.get('error', 'Test error')}")
        
        # Save detailed report to file
        if save_to_file:
            report_path = Path("security_test_report.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Detailed report saved to: {report_path.absolute()}")
        
        return report
    
    def print_recommendations(self, report):
        """Print security recommendations based on test results"""
        print(f"\n🔧 SECURITY RECOMMENDATIONS:")
        print("-" * 40)
        
        if report['summary']['failed'] == 0 and report['summary']['errors'] == 0:
            print("✅ All security tests passed!")
            print("✅ Security patches are working correctly")
            print("✅ No immediate security actions required")
        else:
            print("⚠️  Security vulnerabilities detected!")
            print("🔴 IMMEDIATE ACTIONS REQUIRED:")
            
            if report['failed_tests']:
                print("  1. Review and fix failed security tests")
                for test in report['failed_tests'][:3]:  # Show top 3
                    print(f"     - {test['category']}: {test['test']}")
            
            if report['error_tests']:
                print("  2. Investigate and resolve test errors")
                for test in report['error_tests'][:3]:  # Show top 3
                    print(f"     - {test['category']}: {test['test']}")
            
            print("  3. Re-run tests after fixes are applied")
            print("  4. Consider additional security hardening")
        
        # Category-specific recommendations
        categories = report.get('categories', {})
        for category, stats in categories.items():
            if stats['failed'] > 0 or stats['errors'] > 0:
                if category == 'path_traversal':
                    print("  📁 Path Traversal: Review file path validation and canonicalization")
                elif category == 'race_conditions':
                    print("  🏃 Race Conditions: Check TOCTOU protection and atomic operations")
                elif category == 'input_validation':
                    print("  📝 Input Validation: Strengthen input sanitization and bounds checking")
                elif category == 'symlink_security':
                    print("  🔗 Symlink Security: Verify symlink following restrictions and validation")
                elif category == 'temp_file_security':
                    print("  📄 Temp Files: Review temporary file creation and cleanup procedures")


def main():
    """Main entry point for security test runner"""
    parser = argparse.ArgumentParser(description="Cleanbook Security Test Runner")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose test output")
    parser.add_argument("--category", "-c", type=str,
                       help="Run tests for specific category (path, toctou, size, symlink, temp)")
    parser.add_argument("--quick", "-q", action="store_true",
                       help="Run only essential/quick security tests")
    parser.add_argument("--report", "-r", action="store_true",
                       help="Generate detailed security report")
    parser.add_argument("--no-recommendations", action="store_true",
                       help="Skip security recommendations")
    
    args = parser.parse_args()
    
    # Create test runner
    runner = SecurityTestRunner()
    
    # Create test suite
    suite = runner.create_test_suite(
        category_filter=args.category,
        quick_mode=args.quick
    )
    
    # Run tests
    result, output = runner.run_tests(suite, verbose=args.verbose)
    
    # Generate report
    report = runner.generate_security_report(result, output, save_to_file=args.report)
    
    # Print recommendations
    if not args.no_recommendations:
        runner.print_recommendations(report)
    
    # Exit with appropriate code
    if result.security_results['failed'] or result.security_results['errors']:
        print(f"\n🚨 SECURITY TEST FAILURES DETECTED - Review required!")
        sys.exit(1)
    else:
        print(f"\n✅ ALL SECURITY TESTS PASSED - System secure!")
        sys.exit(0)


if __name__ == "__main__":
    main()