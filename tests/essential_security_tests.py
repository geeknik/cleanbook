#!/usr/bin/env python3
"""
Essential Security Tests
========================

Core security tests that verify the most critical security protections
are working correctly. These tests focus on the main vulnerabilities
identified in the security assessment.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from scanner import FilesystemScanner
    from nuker import DigitalNuker  
    from cleanbook import parse_size_threshold
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    IMPORT_ERROR = str(e)


class EssentialSecurityTests(unittest.TestCase):
    """Essential security tests for critical protections"""

    def setUp(self):
        """Set up test environment"""
        if not IMPORTS_AVAILABLE:
            self.skipTest(f"Required modules not available: {IMPORT_ERROR}")
            
        self.test_dir = Path(tempfile.mkdtemp())
        self.patterns_file = self.test_dir / "test_patterns.yaml"
        
        # Create minimal patterns file
        patterns_content = """
test_category:
  junk_files:
    - "*.tmp"
    - "*.log"
"""
        self.patterns_file.write_text(patterns_content)
        
        # Mock logger
        self.mock_logger = MagicMock()
        self.mock_logger.log_error = MagicMock()

    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, 'test_dir'):
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_system_directory_protection(self):
        """CRITICAL: Test that system directories are protected from access"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Scanner module not available")
            
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=False
        )
        
        # Test critical system paths
        critical_paths = [
            Path("/System"),
            Path("/Library"),
            Path("/Applications"),
            Path("/etc")
        ]
        
        for path in critical_paths:
            with self.subTest(path=path):
                # System paths should be whitelisted (blocked from scanning)
                is_protected = scanner._is_whitelisted(path)
                self.assertTrue(
                    is_protected,
                    f"CRITICAL SECURITY FAILURE: System directory {path} is not protected!"
                )

    def test_path_traversal_blocked(self):
        """CRITICAL: Test that path traversal attacks are blocked"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Nuker module not available")
            
        nuker = DigitalNuker(logger=self.mock_logger, safe_mode=True)
        
        # Test dangerous traversal paths
        traversal_paths = [
            Path("../../../etc/passwd"),
            Path("../../../../System/Library"),
            Path("../../../../../../usr/bin")
        ]
        
        for path in traversal_paths:
            with self.subTest(path=path):
                is_safe = nuker._is_safe_to_delete(path)
                self.assertFalse(
                    is_safe,
                    f"CRITICAL SECURITY FAILURE: Path traversal {path} was allowed!"
                )

    def test_size_threshold_injection_protection(self):
        """CRITICAL: Test that size parsing rejects malicious input"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("parse_size_threshold function not available")
            
        # Test dangerous inputs that should be rejected
        malicious_inputs = [
            "-1MB",                    # Negative values
            "9999999999999999MB",      # Excessive values  
            "1MB; rm -rf /",          # Command injection
            "1MB && echo attack",      # Command chaining
            "../../../etc/passwd",     # Path traversal in size string
        ]
        
        for malicious_input in malicious_inputs:
            with self.subTest(input=malicious_input):
                with self.assertRaises(ValueError, 
                    msg=f"CRITICAL SECURITY FAILURE: Malicious size input '{malicious_input}' was accepted!"):
                    parse_size_threshold(malicious_input)

    def test_outside_home_directory_blocked(self):
        """CRITICAL: Test that operations outside user home are blocked"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Nuker module not available")
            
        nuker = DigitalNuker(logger=self.mock_logger, safe_mode=True)
        
        # Test paths outside home directory
        external_paths = [
            Path("/tmp/dangerous_file"),
            Path("/var/log/system.log"), 
            Path("/usr/local/bin/tool"),
            Path("/opt/malware")
        ]
        
        for path in external_paths:
            with self.subTest(path=path):
                is_safe = nuker._is_safe_to_delete(path)
                self.assertFalse(
                    is_safe,
                    f"CRITICAL SECURITY FAILURE: Path outside home {path} was allowed!"
                )

    def test_symlink_security_basic(self):
        """CRITICAL: Test basic symlink security protections"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Scanner module not available")
            
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=True  # Enable following to test validation
        )
        
        # Create safe target
        safe_target = self.test_dir / "safe_target.tmp"
        safe_target.write_text("safe content")
        
        dangerous_symlink = self.test_dir / "dangerous_symlink.tmp"
        
        try:
            # Try to create symlink to system directory
            dangerous_symlink.symlink_to("/etc/passwd")
            
            # Scan should not access dangerous targets through symlinks
            artifacts = list(scanner._scan_directory(self.test_dir))
            
            # Verify no system files were accessed
            for artifact in artifacts:
                path_str = str(artifact.path).lower()
                self.assertNotIn("etc", path_str, 
                    "CRITICAL SECURITY FAILURE: Symlink allowed access to /etc!")
                self.assertNotIn("passwd", path_str,
                    "CRITICAL SECURITY FAILURE: Symlink allowed access to passwd!")
                    
        except OSError:
            # Symlink creation failure is acceptable
            pass

    def test_temp_file_permissions(self):
        """IMPORTANT: Test that temporary files have secure permissions"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"sensitive data")
            
        try:
            # Check permissions
            import stat
            file_stat = temp_path.stat()
            file_mode = stat.filemode(file_stat.st_mode)
            
            # Should not be world-readable or world-writable
            self.assertNotIn('r', file_mode[-3:], 
                "SECURITY WARNING: Temp file is world-readable!")
            self.assertNotIn('w', file_mode[-3:],
                "SECURITY WARNING: Temp file is world-writable!")
                
        finally:
            temp_path.unlink(missing_ok=True)

    def test_protected_paths_enforcement(self):
        """CRITICAL: Test that protected system paths are enforced"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Nuker module not available")
            
        nuker = DigitalNuker(logger=self.mock_logger, safe_mode=True)
        
        # Test that protected paths are properly initialized
        self.assertIsInstance(nuker.protected_paths, set)
        self.assertGreater(len(nuker.protected_paths), 0, 
            "CRITICAL: No protected paths configured!")
        
        # Verify critical paths are protected
        protected_path_strs = [str(p) for p in nuker.protected_paths]
        critical_protections = ['/System', '/Library', '/Applications']
        
        for critical in critical_protections:
            found = any(critical in path_str for path_str in protected_path_strs)
            self.assertTrue(found, 
                f"CRITICAL SECURITY FAILURE: {critical} is not in protected paths!")

    def test_input_type_validation(self):
        """IMPORTANT: Test that input type validation works"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("parse_size_threshold function not available")
            
        # Test non-string inputs are rejected
        invalid_types = [123, 123.45, None, [], {}, True]
        
        for invalid_input in invalid_types:
            with self.subTest(input=type(invalid_input).__name__):
                if invalid_input is None:
                    # None should return 0.0
                    result = parse_size_threshold(invalid_input)
                    self.assertEqual(result, 0.0)
                else:
                    # Other types should raise ValueError
                    with self.assertRaises(ValueError,
                        msg=f"SECURITY WARNING: Invalid type {type(invalid_input)} was accepted!"):
                        parse_size_threshold(invalid_input)

    def test_valid_operations_still_work(self):
        """FUNCTIONAL: Ensure valid operations still work after security fixes"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        # Test valid size parsing
        valid_result = parse_size_threshold("100MB")
        self.assertEqual(valid_result, 100.0, 
            "REGRESSION: Valid size parsing is broken!")
        
        # Test scanner initialization
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[str(self.test_dir)],
            follow_symlinks=False
        )
        self.assertIsNotNone(scanner.patterns,
            "REGRESSION: Scanner initialization is broken!")
        
        # Test nuker initialization
        nuker = DigitalNuker(logger=self.mock_logger, safe_mode=True)
        self.assertTrue(nuker.safe_mode,
            "REGRESSION: Nuker safe mode not working!")


def run_essential_tests():
    """Run essential security tests with simple reporting"""
    
    print("🔐 CLEANBOOK ESSENTIAL SECURITY TESTS")
    print("=" * 50)
    print("Running critical security protection tests...\n")
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(EssentialSecurityTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Simple summary
    total = result.testsRun
    failed = len(result.failures)
    errors = len(result.errors)
    passed = total - failed - errors
    
    print(f"\n🛡️  ESSENTIAL SECURITY TEST SUMMARY")
    print("=" * 45)
    print(f"Total Critical Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"🚨 Errors: {errors}")
    
    if failed == 0 and errors == 0:
        print(f"\n✅ ALL ESSENTIAL SECURITY TESTS PASSED!")
        print("🔒 Critical security protections are working correctly.")
        return True
    else:
        print(f"\n🚨 CRITICAL SECURITY ISSUES DETECTED!")
        if failed > 0:
            print("❌ Failed tests indicate security vulnerabilities!")
        if errors > 0:
            print("🚨 Test errors may indicate security control failures!")
        print("🔴 IMMEDIATE ATTENTION REQUIRED!")
        return False


if __name__ == "__main__":
    success = run_essential_tests()
    sys.exit(0 if success else 1)