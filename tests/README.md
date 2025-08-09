# Cleanbook Security Test Suite

This directory contains comprehensive security regression tests for the Cleanbook application. These tests verify that all security patches and protections are working correctly and help prevent security regressions in future development.

## 🛡️ Test Coverage

The test suite covers the following security areas identified in the security assessment:

### 1. Path Traversal Protection (`test_path_traversal_protection.py`)
- **CBE-001**: Path traversal attack prevention
- Tests blocking of access to system directories (`/System`, `/Library`, `/Applications`, etc.)
- Validates parent directory traversal detection (`../../../etc/passwd`)
- Ensures symlink-based path traversal is prevented
- Verifies path canonicalization works correctly

### 2. TOCTOU Race Condition Protection (`test_toctou_protection.py`)
- **TOCTOU vulnerabilities**: Time-of-Check-Time-of-Use attack prevention
- Tests file modification detection during deletion process
- Validates atomic operations and stat checking
- Ensures concurrent file access is handled safely
- Tests symlink TOCTOU protection

### 3. Size Threshold Validation (`test_size_threshold_validation.py`)
- **CBE-002**: Integer overflow in size parsing prevention
- Tests rejection of negative values, infinity, and NaN
- Validates bounds checking for excessive values
- Ensures malformed input is properly rejected
- Tests injection attempt detection in size strings

### 4. Symlink Security (`test_symlink_security.py`)
- **CBE-005**: Symlink following attack prevention
- Tests detection and blocking of dangerous symlinks
- Validates symlink target validation outside user home
- Ensures circular symlink protection
- Tests symlink permission bypass prevention

### 5. Secure Temporary File Handling (`test_secure_temp_files.py`)
- Tests secure creation of temporary files and directories
- Validates proper file permissions (600/644, not world-readable)
- Ensures secure cleanup and race condition prevention
- Tests protection against symlink attacks on temp files

## 🚀 Running the Tests

### Run All Security Tests
```bash
# Run complete security test suite
python3 tests/run_security_tests.py

# Run with verbose output
python3 tests/run_security_tests.py --verbose

# Generate detailed report
python3 tests/run_security_tests.py --report
```

### Run Specific Test Categories
```bash
# Run only path traversal tests
python3 tests/run_security_tests.py --category path

# Run only TOCTOU tests
python3 tests/run_security_tests.py --category toctou

# Run only input validation tests
python3 tests/run_security_tests.py --category size

# Run only symlink security tests
python3 tests/run_security_tests.py --category symlink

# Run only temp file security tests
python3 tests/run_security_tests.py --category temp
```

### Quick Security Check
```bash
# Run essential security tests only (faster)
python3 tests/run_security_tests.py --quick
```

### Run Individual Test Files
```bash
# Run specific test file
python3 -m unittest tests.test_path_traversal_protection -v
python3 -m unittest tests.test_toctou_protection -v
python3 -m unittest tests.test_size_threshold_validation -v
python3 -m unittest tests.test_symlink_security -v
python3 -m unittest tests.test_secure_temp_files -v
```

## 📊 Understanding Test Results

### Security Status Indicators
- 🟢 **SECURE**: All tests passed, no vulnerabilities detected
- 🟡 **WARNING**: Minor issues detected, review recommended  
- 🔴 **VULNERABLE**: Security failures detected, immediate action required

### Test Result Categories
- ✅ **Passed**: Security control is working correctly
- ❌ **Failed**: Security vulnerability detected - requires fixing
- 🚨 **Error**: Test execution error - may indicate deeper issues
- ⏭️ **Skipped**: Test skipped (usually due to environment limitations)

### Report Output
The test runner generates:
- **Console Summary**: Overview of test results and security status
- **Detailed JSON Report**: Complete test results saved to `security_test_report.json`
- **Security Recommendations**: Specific actions based on test failures

## 🔧 Test Environment Requirements

### Prerequisites
- Python 3.7+
- All cleanbook dependencies installed
- Write access to temporary directories
- Ability to create symlinks (on some tests)

### Test Data
Tests create temporary files and directories for testing:
- All test data is created in system temp directories
- Cleanup is performed automatically after each test
- No permanent changes are made to the system

## 🛠️ Continuous Integration

### CI/CD Integration
Add to your CI pipeline:
```yaml
# Example GitHub Actions workflow
- name: Run Security Tests
  run: |
    python3 tests/run_security_tests.py --report
    if [ $? -ne 0 ]; then
      echo "Security tests failed!"
      exit 1
    fi
```

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
echo "Running security tests..."
python3 tests/run_security_tests.py --quick
if [ $? -ne 0 ]; then
    echo "Security tests failed. Commit aborted."
    exit 1
fi
```

## 🐛 Debugging Test Failures

### Common Issues
1. **Permission Errors**: Ensure tests can create files in temp directories
2. **Symlink Creation**: Some systems restrict symlink creation - tests will skip
3. **Path Resolution**: Tests may behave differently on different filesystems
4. **Race Conditions**: Timing-sensitive tests may occasionally fail on slow systems

### Debug Mode
Run individual tests with maximum verbosity:
```bash
python3 -m unittest tests.test_path_traversal_protection.TestPathTraversalProtection.test_scanner_blocks_system_directories -v
```

### Test Logs
Check the detailed JSON report for complete error information:
```bash
cat security_test_report.json | jq '.failed_tests'
```

## 📈 Adding New Security Tests

### Test Structure
Each test file should:
1. Import required modules and set up sys.path
2. Create test fixtures in `setUp()` method
3. Clean up test data in `tearDown()` method
4. Use descriptive test method names starting with `test_`
5. Include comprehensive docstrings explaining the security concern

### Example Test Method
```python
def test_new_security_feature(self):
    """Test description of what security control is being validated"""
    # Arrange - set up test data
    malicious_input = "dangerous_value"
    
    # Act - trigger the security control
    result = security_function(malicious_input)
    
    # Assert - verify security control worked
    self.assertIsNone(result, "Malicious input should be rejected")
    self.assertTrue(security_log_contains_warning())
```

### Test Categories
When adding new tests, categorize them appropriately:
- `path_traversal`: File system access controls
- `race_conditions`: TOCTOU and concurrency issues  
- `input_validation`: Input sanitization and bounds checking
- `symlink_security`: Symbolic link handling
- `temp_file_security`: Temporary file creation and cleanup
- `authentication`: User authentication and authorization
- `configuration`: Configuration file security

## 📋 Security Test Checklist

Before considering security tests complete, verify:

- [ ] All identified vulnerabilities from security assessment are tested
- [ ] Edge cases and boundary conditions are covered
- [ ] Both positive (allowed) and negative (blocked) test cases exist
- [ ] Error handling and logging are tested
- [ ] Race conditions and concurrency issues are covered
- [ ] Input validation covers malicious, malformed, and edge case inputs
- [ ] File system security (permissions, paths, symlinks) is thoroughly tested
- [ ] Test cleanup prevents security issues in test environment

## 🔗 Related Documentation

- **Security Assessment Report**: `../SECURITY_ASSESSMENT_REPORT.md`
- **Main Application**: `../cleanbook.py`
- **Scanner Module**: `../utils/scanner.py`
- **Nuker Module**: `../utils/nuker.py`

---

**⚠️ Important Security Note**: These tests verify that security controls are working correctly. Any test failures indicate potential security vulnerabilities that must be addressed immediately before deployment.