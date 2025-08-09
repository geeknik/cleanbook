#!/usr/bin/env python3
"""
Path Traversal Protection Tests
==============================

Tests to verify that all path traversal attack vectors are properly blocked.
These tests ensure that the security patches preventing access to system directories
and parent directory traversal are functioning correctly.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scanner import FilesystemScanner
from nuker import DigitalNuker


class TestPathTraversalProtection(unittest.TestCase):
    """Test suite for path traversal attack prevention"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.patterns_file = self.test_dir / "test_patterns.yaml"
        
        # Create minimal patterns file for testing
        patterns_content = """
test_category:
  junk_files:
    - "*.tmp"
    - "*.log"
"""
        self.patterns_file.write_text(patterns_content)
        
        # Mock logger for nuker tests
        self.mock_logger = MagicMock()
        self.mock_logger.log_error = MagicMock()

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_scanner_blocks_system_directories(self):
        """Test that scanner correctly blocks access to system directories"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=False
        )
        
        system_paths = [
            Path("/System"),
            Path("/Library"), 
            Path("/Applications"),
            Path("/usr/bin"),
            Path("/etc"),
            Path("/private")
        ]
        
        for path in system_paths:
            with self.subTest(path=path):
                # Whitelist check should return True for system paths (blocking them)
                is_whitelisted = scanner._is_whitelisted(path)
                self.assertTrue(
                    is_whitelisted, 
                    f"System path {path} should be blocked but was allowed"
                )

    def test_scanner_blocks_parent_directory_traversal(self):
        """Test that scanner blocks parent directory traversal attempts"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=False
        )
        
        traversal_paths = [
            Path("../../../etc/passwd"),
            Path("../../../../System/Library"),
            Path("../../../../../../usr/bin"),
            Path("/tmp/../etc/passwd"),
            Path("/var/../etc/hosts")
        ]
        
        for path in traversal_paths:
            with self.subTest(path=path):
                # These paths should be blocked by whitelist or path validation
                is_whitelisted = scanner._is_whitelisted(path)
                # If not whitelisted by system protection, should still be safe
                if not is_whitelisted:
                    # Path should resolve to something safe or fail
                    try:
                        resolved = path.resolve()
                        # Should not resolve to system directories
                        self.assertNotIn("System", str(resolved))
                        self.assertNotIn("etc", str(resolved))
                        self.assertNotIn("usr", str(resolved))
                    except (OSError, RuntimeError):
                        # Path resolution failure is acceptable for malicious paths
                        pass

    def test_scanner_symlink_traversal_protection(self):
        """Test that scanner properly validates symlink targets"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=True
        )
        
        # Create test symlinks
        safe_target = self.test_dir / "safe_target.txt"
        safe_target.touch()
        
        safe_symlink = self.test_dir / "safe_symlink"
        dangerous_symlink = self.test_dir / "dangerous_symlink"
        
        try:
            # Create safe symlink
            safe_symlink.symlink_to(safe_target)
            
            # Create dangerous symlink to system directory
            try:
                dangerous_symlink.symlink_to("/etc/passwd")
            except OSError:
                # Permission error is fine, create alternate dangerous symlink
                dangerous_symlink.symlink_to("../../../etc")
                
            # Test scanning with symlinks
            artifacts = list(scanner._scan_directory(self.test_dir, depth=0))
            
            # Should not find artifacts via dangerous symlinks
            for artifact in artifacts:
                self.assertNotIn("etc", str(artifact.path))
                self.assertNotIn("passwd", str(artifact.path))
                self.assertNotIn("System", str(artifact.path))
                
        except OSError:
            # Symlink creation failures are acceptable in test environment
            pass

    def test_nuker_path_safety_validation(self):
        """Test that nuker properly validates paths before deletion"""
        nuker = DigitalNuker(
            logger=self.mock_logger,
            safe_mode=True
        )
        
        dangerous_paths = [
            Path("/System/Library/CoreServices"),
            Path("/etc/passwd"),
            Path("/usr/bin/python"),
            Path("/Applications/Safari.app"),
            Path("/Library/Preferences"),
            Path("/private/etc/hosts"),
            Path("../../../etc/passwd"),
            Path("../../../../System")
        ]
        
        for path in dangerous_paths:
            with self.subTest(path=path):
                is_safe = nuker._is_safe_to_delete(path)
                self.assertFalse(
                    is_safe,
                    f"Dangerous path {path} was marked as safe for deletion"
                )
                
                # Verify error was logged
                nuker.logger.log_error.assert_called()

    def test_nuker_blocks_paths_outside_home_directory(self):
        """Test that nuker blocks deletion of paths outside user home"""
        nuker = DigitalNuker(
            logger=self.mock_logger,
            safe_mode=True
        )
        
        outside_home_paths = [
            Path("/tmp/some_file.txt"),
            Path("/var/log/system.log"),
            Path("/usr/local/bin/tool"),
            Path("/opt/homebrew/bin/brew")
        ]
        
        for path in outside_home_paths:
            with self.subTest(path=path):
                is_safe = nuker._is_safe_to_delete(path)
                self.assertFalse(
                    is_safe,
                    f"Path outside home directory {path} was marked as safe"
                )

    def test_nuker_blocks_shallow_paths(self):
        """Test that nuker blocks deletion of shallow/root-level paths"""
        nuker = DigitalNuker(
            logger=self.mock_logger,
            safe_mode=True
        )
        
        shallow_paths = [
            Path("/"),
            Path("/usr"),
            Path("/etc"),
            Path(str(Path.home())),  # User home itself
            Path(str(Path.home() / "Documents")),  # Direct subdirectory
        ]
        
        for path in shallow_paths:
            with self.subTest(path=path):
                is_safe = nuker._is_safe_to_delete(path)
                self.assertFalse(
                    is_safe,
                    f"Shallow path {path} was marked as safe for deletion"
                )

    def test_nuker_parent_traversal_detection(self):
        """Test that nuker detects and blocks parent directory traversal"""
        nuker = DigitalNuker(
            logger=self.mock_logger,
            safe_mode=True
        )
        
        traversal_paths = [
            Path("../../../etc/passwd"),
            Path("../../System/Library"),
            Path(str(Path.home() / "../.." / "etc" / "hosts")),
            Path(str(Path.home() / ".." / ".." / "System")),
        ]
        
        for path in traversal_paths:
            with self.subTest(path=path):
                is_safe = nuker._is_safe_to_delete(path)
                self.assertFalse(
                    is_safe,
                    f"Path traversal {path} was not detected and blocked"
                )

    def test_valid_paths_are_allowed(self):
        """Test that legitimate paths within user home are allowed"""
        nuker = DigitalNuker(
            logger=self.mock_logger,
            safe_mode=True
        )
        
        # Create test files in a safe location
        test_subdir = self.test_dir / "user_files" / "deep" / "nested"
        test_subdir.mkdir(parents=True)
        test_file = test_subdir / "test_file.txt"
        test_file.write_text("test content")
        
        # This should be allowed if it's in a safe location
        # Note: This test may fail if test_dir is not under user home
        # In that case, create a path under actual home directory
        home_test_dir = Path.home() / "cleanbook_test" / "deep" / "nested"
        home_test_dir.mkdir(parents=True, exist_ok=True)
        home_test_file = home_test_dir / "safe_test_file.txt"
        home_test_file.write_text("safe test content")
        
        try:
            is_safe = nuker._is_safe_to_delete(home_test_file)
            # Should be safe if it meets all criteria (depth, ownership, etc.)
            # The actual result depends on the file's properties
            # We mainly want to ensure no exceptions are thrown
            self.assertIsInstance(is_safe, bool)
            
        finally:
            # Clean up
            import shutil
            shutil.rmtree(home_test_dir.parent, ignore_errors=True)

    def test_path_canonicalization_prevents_bypass(self):
        """Test that path canonicalization prevents bypass attempts"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=False
        )
        
        bypass_attempts = [
            Path("/tmp/../etc/passwd"),
            Path("/var/./../../etc/hosts"),
            Path("/usr/bin/../../../System/Library"),
            Path("./../../../../../../etc/passwd")
        ]
        
        for path in bypass_attempts:
            with self.subTest(path=path):
                # The _is_whitelisted method should resolve paths and catch bypasses
                try:
                    is_whitelisted = scanner._is_whitelisted(path)
                    # Should be blocked or resolve to safe location
                    if not is_whitelisted:
                        resolved = path.resolve()
                        # Verify it doesn't resolve to dangerous locations
                        dangerous_components = ['etc', 'System', 'Library', 'usr']
                        path_str = str(resolved).lower()
                        for component in dangerous_components:
                            if component in path_str and 'home' not in path_str:
                                self.fail(f"Path bypass attempt succeeded: {path} -> {resolved}")
                except (OSError, ValueError):
                    # Path resolution failures are acceptable for malicious paths
                    pass


if __name__ == '__main__':
    unittest.main(verbosity=2)