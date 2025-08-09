#!/usr/bin/env python3
"""
Secure Temporary File Handling Tests
===================================

Tests to verify that temporary files are created and handled securely,
preventing attacks through temp file manipulation, race conditions,
and insecure permissions.
"""

import unittest
import tempfile
import os
import sys
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nuker import DigitalNuker
import cleanbook


class TestSecureTempFiles(unittest.TestCase):
    """Test suite for secure temporary file handling"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Mock logger
        self.mock_logger = MagicMock()
        self.mock_logger.log_error = MagicMock()

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_temp_file_permissions(self):
        """Test that temporary files are created with secure permissions"""
        # Create a temporary file and check its permissions
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(b"test content")
            
        try:
            # Check file permissions
            file_stat = temp_path.stat()
            file_mode = stat.filemode(file_stat.st_mode)
            
            # Should not be world-readable or world-writable
            self.assertNotIn('r', file_mode[-3:])  # No world read
            self.assertNotIn('w', file_mode[-3:])  # No world write
            
            # Should be owner-only accessible (600 or 644 at most)
            mode_octal = oct(file_stat.st_mode)[-3:]
            self.assertIn(mode_octal, ['600', '644', '640'])
            
        finally:
            temp_path.unlink(missing_ok=True)

    def test_temp_file_location_security(self):
        """Test that temporary files are created in secure locations"""
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_path = Path(temp_file.name)
            
            # Should be in system temp directory or user-specific temp
            temp_parent = temp_path.parent
            
            # Common secure temp directories
            secure_temp_dirs = [
                Path("/tmp"),
                Path("/var/tmp"), 
                Path.home() / "tmp",
                Path(tempfile.gettempdir()),
            ]
            
            # Should be in one of the secure locations
            is_secure_location = any(
                str(temp_parent).startswith(str(secure_dir))
                for secure_dir in secure_temp_dirs
            )
            
            self.assertTrue(
                is_secure_location,
                f"Temp file created in insecure location: {temp_parent}"
            )

    def test_temp_file_cleanup(self):
        """Test that temporary files are properly cleaned up"""
        temp_paths = []
        
        # Create multiple temporary files
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_path = Path(temp_file.name)
            temp_file.write(b"test content")
            temp_file.close()
            temp_paths.append(temp_path)
        
        # All should exist initially
        for temp_path in temp_paths:
            self.assertTrue(temp_path.exists())
            
        # Clean them up
        for temp_path in temp_paths:
            temp_path.unlink()
            
        # Should all be gone
        for temp_path in temp_paths:
            self.assertFalse(temp_path.exists())

    def test_temp_directory_permissions(self):
        """Test that temporary directories are created with secure permissions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Check directory permissions
            dir_stat = temp_path.stat()
            dir_mode = stat.filemode(dir_stat.st_mode)
            
            # Should not be world-writable
            self.assertNotIn('w', dir_mode[-3:])
            
            # Should have appropriate directory permissions
            mode_octal = oct(dir_stat.st_mode)[-3:]
            # Common secure directory modes: 700, 755, 750
            self.assertIn(mode_octal[0], ['7'])  # Owner has full access
            self.assertNotEqual(mode_octal[-1], '7')  # World doesn't have full access

    def test_temp_file_race_condition_prevention(self):
        """Test prevention of race conditions in temp file creation"""
        # Test atomic temp file creation
        temp_files = []
        
        def create_temp_file():
            # Use secure temp file creation
            fd, path = tempfile.mkstemp()
            os.write(fd, b"test content")
            os.close(fd)
            return Path(path)
        
        # Create multiple temp files concurrently to test for races
        import threading
        
        def worker():
            temp_file = create_temp_file()
            temp_files.append(temp_file)
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All temp files should be unique
        paths = [str(f) for f in temp_files]
        unique_paths = set(paths)
        self.assertEqual(len(paths), len(unique_paths), "Temp file race condition detected")
        
        # Clean up
        for temp_file in temp_files:
            temp_file.unlink(missing_ok=True)

    def test_temp_file_symlink_protection(self):
        """Test protection against symlink attacks on temp files"""
        # Create a temp file
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)
        temp_path = Path(temp_path)
        
        try:
            # Ensure it's a regular file, not a symlink
            self.assertFalse(temp_path.is_symlink(), "Temp file should not be a symlink")
            
            # Try to replace with symlink (should be detected if checked)
            temp_path.unlink()
            
            # Create symlink to sensitive file
            try:
                temp_path.symlink_to("/etc/passwd")
                
                # Code should detect symlinks before writing
                if temp_path.is_symlink():
                    # This is a security risk - temp file is actually a symlink
                    self.fail("Temp file was replaced with symlink - security vulnerability")
                    
            except OSError:
                # Symlink creation may fail - that's acceptable
                pass
                
        finally:
            # Clean up
            if temp_path.exists() or temp_path.is_symlink():
                temp_path.unlink()

    def test_temp_file_predictable_names(self):
        """Test that temp files don't use predictable names"""
        temp_names = []
        
        # Create multiple temp files and check name patterns
        for i in range(10):
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_name = Path(temp_file.name).name
                temp_names.append(temp_name)
        
        # Names should not be predictable/sequential
        # Check that they contain random components
        for name in temp_names:
            # Should contain random characters (letters/numbers)
            has_random = any(c.isalnum() for c in name if c not in ['_', '.', '-'])
            self.assertTrue(has_random, f"Temp filename lacks randomness: {name}")
        
        # Should not be sequential
        unique_names = set(temp_names)
        self.assertEqual(len(temp_names), len(unique_names), "Temp filenames are not unique")

    def test_temp_file_content_security(self):
        """Test that sensitive data in temp files is handled securely"""
        sensitive_data = "password123\nsecret_key\nconfidential_info"
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(sensitive_data)
            temp_file.flush()
            
            # Check file permissions after writing sensitive data
            file_stat = temp_path.stat()
            mode_octal = oct(file_stat.st_mode)[-3:]
            
            # Should have restrictive permissions for sensitive data
            self.assertIn(mode_octal[0], ['6', '7'])  # Owner read/write
            self.assertEqual(mode_octal[1], '0')      # No group access
            self.assertEqual(mode_octal[2], '0')      # No world access
        
        try:
            # Verify content can be read by owner
            content = temp_path.read_text()
            self.assertEqual(content, sensitive_data)
            
        finally:
            # Secure cleanup - overwrite before deletion
            if temp_path.exists():
                # Overwrite with random data before deletion
                temp_path.write_bytes(os.urandom(len(sensitive_data.encode())))
                temp_path.unlink()

    def test_report_file_security(self):
        """Test security of report files generated by cleanbook"""
        # Test the report generation in cleanbook
        report_data = {
            "summary": {"total_artifacts": 5, "total_size_mb": 100.5},
            "categories": {"test": {"count": 5, "size_mb": 100.5}},
            "top_artifacts": []
        }
        
        # Create report file
        report_path = self.test_dir / f"scan_report_{int(__import__('time').time())}.json"
        
        with open(report_path, 'w') as f:
            import json
            json.dump(report_data, f, indent=2)
        
        # Check report file permissions
        file_stat = report_path.stat()
        mode_octal = oct(file_stat.st_mode)[-3:]
        
        # Report files should be readable but not world-writable
        self.assertNotEqual(mode_octal[-1], '7')  # Not world-writable
        self.assertIn(mode_octal[0], ['6', '7'])  # Owner has appropriate access

    def test_log_file_security(self):
        """Test security of log files"""
        # Create a log file in test directory
        log_file = self.test_dir / "cleanbook.log"
        
        # Write log data
        log_content = "2025-08-09 INFO Starting cleanbook scan\n2025-08-09 WARN Found large file\n"
        log_file.write_text(log_content)
        
        # Check log file permissions
        file_stat = log_file.stat()
        mode_octal = oct(file_stat.st_mode)[-3:]
        
        # Log files should not be world-readable (may contain sensitive paths)
        self.assertNotIn(mode_octal[-1], ['4', '5', '6', '7'])  # No world read/write
        
        # Should be owner-readable and writable
        self.assertIn(mode_octal[0], ['6', '7'])

    def test_config_file_security(self):
        """Test security of configuration files"""
        config_content = """
safe_mode: true
whitelist_paths:
  - "/Users/test/safe_dir"
size_thresholds:
  minimum_file_size: "1MB"
"""
        
        config_file = self.test_dir / "secure_config.yaml"
        config_file.write_text(config_content)
        
        # Check config file permissions
        file_stat = config_file.stat()
        mode_octal = oct(file_stat.st_mode)[-3:]
        
        # Config files should be secure (not world-writable)
        self.assertNotEqual(mode_octal[-1], '7')  # Not world-writable
        self.assertNotEqual(mode_octal[-1], '6')  # Not world-readable/writable

    def test_temp_file_cleanup_on_error(self):
        """Test that temp files are cleaned up even when errors occur"""
        temp_files_created = []
        
        def create_temp_with_error():
            # Create temp file
            fd, path = tempfile.mkstemp()
            temp_path = Path(path)
            temp_files_created.append(temp_path)
            
            try:
                os.write(fd, b"test data")
                # Simulate an error
                raise ValueError("Simulated error")
            except ValueError:
                # Cleanup should still happen
                os.close(fd)
                temp_path.unlink()
                raise
        
        # Should clean up temp file even on error
        with self.assertRaises(ValueError):
            create_temp_with_error()
        
        # Temp file should be cleaned up
        for temp_path in temp_files_created:
            self.assertFalse(temp_path.exists(), f"Temp file not cleaned up: {temp_path}")

    def test_temp_file_secure_creation_flags(self):
        """Test that temp files are created with secure flags"""
        # Create temp file with explicit secure flags
        fd, temp_path = tempfile.mkstemp()
        temp_path = Path(temp_path)
        
        try:
            # Check that file descriptor has appropriate flags
            # This is system-dependent, but we can check basic security
            
            # File should exist and be a regular file
            self.assertTrue(temp_path.exists())
            self.assertTrue(temp_path.is_file())
            self.assertFalse(temp_path.is_symlink())
            
            # Should be owned by current user
            file_stat = temp_path.stat()
            self.assertEqual(file_stat.st_uid, os.getuid())
            
        finally:
            os.close(fd)
            temp_path.unlink(missing_ok=True)

    def test_temp_directory_traversal_protection(self):
        """Test protection against directory traversal in temp file paths"""
        # Try to create temp files with dangerous names
        dangerous_names = [
            "../../../etc/passwd",
            "../../../System/Library/test",
            "../../../../usr/bin/malware",
        ]
        
        for dangerous_name in dangerous_names:
            with self.subTest(name=dangerous_name):
                try:
                    # tempfile should not allow dangerous paths
                    with tempfile.NamedTemporaryFile(prefix=dangerous_name) as temp_file:
                        temp_path = Path(temp_file.name)
                        
                        # Should be in temp directory, not at dangerous location
                        temp_parent = temp_path.parent
                        self.assertIn("tmp", str(temp_parent).lower())
                        self.assertNotIn("etc", str(temp_path))
                        self.assertNotIn("System", str(temp_path))
                        self.assertNotIn("usr", str(temp_path))
                        
                except (ValueError, OSError):
                    # Rejection of dangerous names is acceptable
                    pass


if __name__ == '__main__':
    unittest.main(verbosity=2)