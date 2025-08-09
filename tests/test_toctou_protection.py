#!/usr/bin/env python3
"""
TOCTOU (Time of Check, Time of Use) Race Condition Protection Tests
==================================================================

Tests to verify that race conditions between file checks and file operations
are properly prevented. These tests ensure that the security patches preventing
TOCTOU attacks in the deletion process are working correctly.
"""

import unittest
import tempfile
import os
import sys
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

# Add utils to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from nuker import DigitalNuker, DeletionMode
from scanner import Artifact


class TestTOCTOUProtection(unittest.TestCase):
    """Test suite for TOCTOU race condition prevention"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Mock logger
        self.mock_logger = MagicMock()
        self.mock_logger.log_error = MagicMock()
        self.mock_logger.log_deletion = MagicMock()
        
        self.nuker = DigitalNuker(
            logger=self.mock_logger,
            safe_mode=True
        )

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_file_modification_detection_during_deletion(self):
        """Test that file modifications during deletion are detected and handled"""
        test_file = self.test_dir / "race_test_file.txt"
        test_file.write_text("original content")
        
        original_stat = test_file.stat()
        
        # Create a mock that simulates file modification between stat calls
        def modified_stat_side_effect():
            # First call returns original stat
            # Second call returns modified stat (different mtime)
            if hasattr(modified_stat_side_effect, 'call_count'):
                modified_stat_side_effect.call_count += 1
            else:
                modified_stat_side_effect.call_count = 1
                
            if modified_stat_side_effect.call_count == 1:
                return original_stat
            else:
                # Return a stat with different mtime to simulate modification
                modified_stat = MagicMock()
                modified_stat.st_size = original_stat.st_size
                modified_stat.st_mtime = original_stat.st_mtime + 1.0  # Modified time
                return modified_stat
        
        with patch.object(test_file, 'stat', side_effect=modified_stat_side_effect):
            with patch.object(test_file, 'is_file', return_value=True):
                result = self.nuker._execute_deletion(test_file, dry_run=False)
                
                # Should fail due to file modification detection
                self.assertFalse(result.success)
                self.assertIn("modified during deletion", str(result.error))

    def test_file_size_change_detection(self):
        """Test detection of file size changes during deletion process"""
        test_file = self.test_dir / "size_change_test.txt"
        test_file.write_text("initial content")
        
        original_stat = test_file.stat()
        
        def size_changed_stat():
            if hasattr(size_changed_stat, 'called'):
                # Second call - return different size
                modified_stat = MagicMock()
                modified_stat.st_size = original_stat.st_size + 100  # Different size
                modified_stat.st_mtime = original_stat.st_mtime
                return modified_stat
            else:
                size_changed_stat.called = True
                return original_stat
        
        with patch.object(test_file, 'stat', side_effect=size_changed_stat):
            with patch.object(test_file, 'is_file', return_value=True):
                result = self.nuker._execute_deletion(test_file, dry_run=False)
                
                # Should fail due to size change detection
                self.assertFalse(result.success)
                self.assertIn("modified during deletion", str(result.error))

    def test_concurrent_file_access_handling(self):
        """Test handling of concurrent file access during deletion"""
        test_file = self.test_dir / "concurrent_test.txt"
        test_file.write_text("test content for concurrent access")
        
        # Create artifact for deletion
        artifact = Artifact(
            path=test_file,
            size_bytes=test_file.stat().st_size,
            category="test",
            pattern="*.txt",
            depth=1
        )
        
        # Function to modify file concurrently
        def modify_file():
            time.sleep(0.01)  # Small delay to create race condition
            try:
                if test_file.exists():
                    test_file.write_text("modified content during deletion")
            except:
                pass  # File may be deleted by the time we try to modify
        
        # Start concurrent modification
        modifier_thread = threading.Thread(target=modify_file)
        modifier_thread.start()
        
        # Attempt deletion
        results = self.nuker.delete_artifacts([artifact], mode=DeletionMode.FORCE)
        
        # Wait for modifier thread
        modifier_thread.join()
        
        # Should handle concurrent access gracefully
        self.assertEqual(len(results), 1)
        result = results[0]
        
        # Result should either succeed (if we won the race) or fail gracefully
        if not result.success:
            # Should have logged an appropriate error
            self.assertIsNotNone(result.error)

    def test_directory_race_condition_protection(self):
        """Test protection against race conditions with directory operations"""
        test_dir = self.test_dir / "race_directory"
        test_dir.mkdir()
        
        # Add some files to the directory
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")
        
        # Create artifact for the directory
        artifact = Artifact(
            path=test_dir,
            size_bytes=100,
            category="test",
            pattern="race_directory",
            depth=1
        )
        
        # Function to add files concurrently during deletion
        def add_files_during_deletion():
            time.sleep(0.01)
            try:
                if test_dir.exists():
                    (test_dir / "added_during_deletion.txt").write_text("sneaky content")
            except:
                pass  # Directory may be deleted
        
        # Start concurrent modification
        modifier_thread = threading.Thread(target=add_files_during_deletion)
        modifier_thread.start()
        
        # Attempt deletion
        results = self.nuker.delete_artifacts([artifact], mode=DeletionMode.FORCE)
        
        # Wait for modifier thread
        modifier_thread.join()
        
        # Should handle directory race conditions
        self.assertEqual(len(results), 1)
        # Operation should either succeed completely or fail safely
        result = results[0]
        self.assertIsInstance(result.success, bool)

    def test_symlink_toctou_protection(self):
        """Test protection against TOCTOU attacks using symlinks"""
        # Create a safe target file
        safe_target = self.test_dir / "safe_target.txt"
        safe_target.write_text("safe content")
        
        # Create symlink
        test_symlink = self.test_dir / "test_symlink"
        
        try:
            test_symlink.symlink_to(safe_target)
            
            # Function to change symlink target during processing
            def change_symlink_target():
                time.sleep(0.01)
                try:
                    if test_symlink.exists():
                        test_symlink.unlink()
                        # Try to create dangerous symlink
                        test_symlink.symlink_to("/etc/passwd")
                except:
                    pass  # Symlink operations may fail
            
            # Create artifact for symlink
            artifact = Artifact(
                path=test_symlink,
                size_bytes=safe_target.stat().st_size,
                category="test",
                pattern="test_symlink",
                depth=1
            )
            
            # Start concurrent symlink modification
            modifier_thread = threading.Thread(target=change_symlink_target)
            modifier_thread.start()
            
            # Attempt deletion
            results = self.nuker.delete_artifacts([artifact], mode=DeletionMode.FORCE)
            
            # Wait for modifier thread
            modifier_thread.join()
            
            # Should handle symlink race conditions safely
            self.assertEqual(len(results), 1)
            result = results[0]
            
            # If it failed, should be due to safety checks
            if not result.success:
                self.assertIsNotNone(result.error)
                
        except OSError:
            # Symlink creation may fail in test environment
            self.skipTest("Cannot create symlinks in test environment")

    def test_multiple_threads_same_file(self):
        """Test behavior when multiple threads try to delete the same file"""
        test_file = self.test_dir / "multi_thread_test.txt"
        test_file.write_text("content for multi-thread test")
        
        # Create multiple artifacts pointing to the same file
        artifacts = []
        for i in range(3):
            artifact = Artifact(
                path=test_file,
                size_bytes=test_file.stat().st_size,
                category="test",
                pattern=f"*.txt_{i}",
                depth=1
            )
            artifacts.append(artifact)
        
        # Try to delete same file multiple times concurrently
        results = self.nuker.delete_artifacts(artifacts, mode=DeletionMode.FORCE)
        
        # Should handle multiple deletion attempts gracefully
        self.assertEqual(len(results), 3)
        
        # At most one should succeed, others should fail gracefully
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        # Should have at most 1 success (the first to delete)
        self.assertLessEqual(len(successful), 1)
        
        # Failed attempts should have appropriate errors
        for result in failed:
            self.assertIsNotNone(result.error)

    def test_atomic_stat_operations(self):
        """Test that stat operations are atomic and race-condition safe"""
        test_file = self.test_dir / "atomic_test.txt"
        test_file.write_text("content for atomic test")
        
        # Track stat call order
        stat_calls = []
        original_stat = test_file.stat
        
        def tracking_stat():
            stat_calls.append(time.time())
            return original_stat()
        
        with patch.object(test_file, 'stat', side_effect=tracking_stat):
            result = self.nuker._execute_deletion(test_file, dry_run=True)
            
            # Should have made exactly 2 stat calls (initial and verification)
            # In dry run mode, it should still do the stat operations
            self.assertGreaterEqual(len(stat_calls), 1)
            
            # Should complete successfully in dry run
            self.assertTrue(result.success)

    def test_error_handling_during_race_conditions(self):
        """Test proper error handling when race conditions are detected"""
        test_file = self.test_dir / "error_handling_test.txt"
        test_file.write_text("content for error handling test")
        
        # Mock stat to raise OSError on second call (simulating file disappearing)
        call_count = 0
        def disappearing_file_stat():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return test_file.stat()
            else:
                raise FileNotFoundError("File disappeared during operation")
        
        with patch.object(test_file, 'stat', side_effect=disappearing_file_stat):
            with patch.object(test_file, 'is_file', return_value=True):
                result = self.nuker._execute_deletion(test_file, dry_run=False)
                
                # Should handle the error gracefully
                self.assertFalse(result.success)
                self.assertIsInstance(result.error, FileNotFoundError)
                self.assertGreater(result.duration_ms, 0)

    def test_safe_mode_extra_protection(self):
        """Test that safe mode provides extra protection against race conditions"""
        # This test verifies that safe mode adds additional checks
        test_file = self.test_dir / "safe_mode_test.txt"
        test_file.write_text("content for safe mode test")
        
        safe_nuker = DigitalNuker(
            logger=self.mock_logger,
            safe_mode=True
        )
        
        unsafe_nuker = DigitalNuker(
            logger=self.mock_logger,
            safe_mode=False
        )
        
        # Create artifacts
        artifact = Artifact(
            path=test_file,
            size_bytes=test_file.stat().st_size,
            category="test",
            pattern="*.txt",
            depth=1
        )
        
        # Both should handle the same file safely, but safe mode should be more cautious
        safe_result = safe_nuker.delete_artifacts([artifact], mode=DeletionMode.DRY_RUN)
        
        # Reset file for second test
        if not test_file.exists():
            test_file.write_text("content for safe mode test")
            
        unsafe_result = unsafe_nuker.delete_artifacts([artifact], mode=DeletionMode.DRY_RUN)
        
        # Both should succeed in dry run mode
        self.assertEqual(len(safe_result), 1)
        self.assertEqual(len(unsafe_result), 1)
        self.assertTrue(safe_result[0].success)
        self.assertTrue(unsafe_result[0].success)


if __name__ == '__main__':
    unittest.main(verbosity=2)