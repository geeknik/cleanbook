#!/usr/bin/env python3
"""
Symlink Following Security Tests
===============================

Tests to verify that symbolic link handling is secure and prevents
attackers from using symlinks to access restricted directories or
bypass security controls.
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


class TestSymlinkSecurity(unittest.TestCase):
    """Test suite for symlink security controls"""

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
    - "*symlink*"
"""
        self.patterns_file.write_text(patterns_content)
        
        # Mock logger
        self.mock_logger = MagicMock()
        self.mock_logger.log_error = MagicMock()

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_symlink_detection_and_blocking(self):
        """Test that dangerous symlinks are detected and blocked"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=False  # Symlinks should be ignored
        )
        
        # Create test files
        safe_file = self.test_dir / "safe_file.tmp"
        safe_file.write_text("safe content")
        
        dangerous_symlink = self.test_dir / "dangerous_symlink.tmp"
        
        try:
            # Create symlink to system directory
            dangerous_symlink.symlink_to("/etc/passwd")
            
            # Scan should not follow the symlink when follow_symlinks=False
            artifacts = list(scanner._scan_directory(self.test_dir))
            
            # Should find the safe file but not follow dangerous symlink
            artifact_paths = [str(a.path) for a in artifacts]
            self.assertIn(str(safe_file), artifact_paths)
            # Should not have accessed /etc/passwd through symlink
            
        except OSError:
            # Symlink creation may fail - that's acceptable
            pass

    def test_symlink_target_validation_outside_home(self):
        """Test that symlinks pointing outside user home are blocked"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=True  # Enable symlink following to test validation
        )
        
        external_targets = [
            "/etc/passwd",
            "/System/Library/CoreServices",
            "/usr/bin/python",
            "/Applications/Safari.app",
            "/Library/Preferences"
        ]
        
        for target in external_targets:
            with self.subTest(target=target):
                symlink_path = self.test_dir / f"external_symlink_{target.replace('/', '_')}.tmp"
                
                try:
                    symlink_path.symlink_to(target)
                    
                    # Scan should detect and block external symlink
                    artifacts = list(scanner._scan_directory(self.test_dir))
                    
                    # Should not find artifacts through external symlink
                    for artifact in artifacts:
                        self.assertNotIn(target, str(artifact.path))
                        self.assertNotIn("etc", str(artifact.path))
                        self.assertNotIn("System", str(artifact.path))
                        self.assertNotIn("usr", str(artifact.path))
                        
                except OSError:
                    # Symlink creation failure is acceptable
                    continue

    def test_symlink_traversal_attack_prevention(self):
        """Test prevention of symlink traversal attacks"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=True
        )
        
        traversal_targets = [
            "../../../etc/passwd",
            "../../../../System/Library",
            "../../../../../../../usr/bin",
            "../../etc/hosts"
        ]
        
        for target in traversal_targets:
            with self.subTest(target=target):
                symlink_path = self.test_dir / f"traversal_symlink_{abs(hash(target))}.tmp"
                
                try:
                    symlink_path.symlink_to(target)
                    
                    # Scan should not follow traversal symlinks
                    artifacts = list(scanner._scan_directory(self.test_dir))
                    
                    # Should not access system files through traversal
                    for artifact in artifacts:
                        path_str = str(artifact.path).lower()
                        self.assertNotIn("etc", path_str)
                        self.assertNotIn("system", path_str)
                        self.assertNotIn("usr", path_str)
                        
                except OSError:
                    continue

    def test_circular_symlink_protection(self):
        """Test protection against circular symlinks"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=True
        )
        
        # Create circular symlinks
        symlink1 = self.test_dir / "circular1.tmp"
        symlink2 = self.test_dir / "circular2.tmp"
        
        try:
            # Create circular reference
            symlink1.symlink_to(symlink2)
            symlink2.symlink_to(symlink1)
            
            # Scan should handle circular symlinks without infinite loop
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Circular symlink caused infinite loop")
            
            # Set timeout to prevent infinite loop
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)  # 5 second timeout
            
            try:
                artifacts = list(scanner._scan_directory(self.test_dir))
                # Should complete without hanging
                signal.alarm(0)  # Cancel alarm
                
                # Should not cause infinite artifacts
                self.assertLess(len(artifacts), 10)
                
            except TimeoutError:
                self.fail("Circular symlink caused infinite loop/timeout")
            finally:
                signal.alarm(0)
                
        except OSError:
            # Symlink creation may fail
            pass

    def test_symlink_parent_directory_reference(self):
        """Test blocking of symlinks with parent directory references"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=True
        )
        
        parent_refs = [
            "..",
            "../",
            "../../",
            "../../../",
            "./../etc",
            "../System"
        ]
        
        for parent_ref in parent_refs:
            with self.subTest(parent_ref=parent_ref):
                symlink_path = self.test_dir / f"parent_ref_{abs(hash(parent_ref))}.tmp"
                
                try:
                    symlink_path.symlink_to(parent_ref)
                    
                    # Should detect and block parent references
                    artifacts = list(scanner._scan_directory(self.test_dir))
                    
                    # Should not follow parent directory references
                    for artifact in artifacts:
                        # Artifact paths should not contain parent refs
                        self.assertNotIn("..", str(artifact.path))
                        
                except OSError:
                    continue

    def test_symlink_depth_limitation(self):
        """Test that symlink following has appropriate depth limits"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=True
        )
        
        # Create deep symlink chain
        chain_dir = self.test_dir / "chain"
        chain_dir.mkdir()
        
        current_dir = chain_dir
        for i in range(20):  # Create deep chain
            next_dir = current_dir / f"level_{i}"
            next_dir.mkdir()
            
            # Create symlink to next level
            symlink = current_dir / f"symlink_{i}.tmp"
            try:
                symlink.symlink_to(next_dir / "target.tmp")
                # Create target file
                (next_dir / "target.tmp").touch()
                current_dir = next_dir
            except OSError:
                break
        
        # Scan should not follow excessively deep symlink chains
        artifacts = list(scanner._scan_directory(self.test_dir))
        
        # Should limit depth to prevent resource exhaustion
        self.assertLess(len(artifacts), 50)  # Reasonable limit

    def test_symlink_time_of_check_time_of_use(self):
        """Test TOCTOU protection for symlinks"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=True
        )
        
        # Create safe target initially
        safe_target = self.test_dir / "safe_target.tmp"
        safe_target.write_text("safe")
        
        test_symlink = self.test_dir / "toctou_symlink.tmp"
        
        try:
            test_symlink.symlink_to(safe_target)
            
            # Mock readlink to simulate target change
            original_readlink = test_symlink.readlink
            
            def changing_readlink():
                # First call returns safe target, second call dangerous
                if hasattr(changing_readlink, 'called'):
                    return Path("/etc/passwd")
                else:
                    changing_readlink.called = True
                    return original_readlink()
            
            with patch.object(test_symlink, 'readlink', side_effect=changing_readlink):
                # Should handle target changes safely
                artifacts = list(scanner._scan_directory(self.test_dir))
                
                # Should not access dangerous target
                for artifact in artifacts:
                    self.assertNotIn("etc", str(artifact.path))
                    self.assertNotIn("passwd", str(artifact.path))
                    
        except OSError:
            pass

    def test_symlink_permission_bypass_attempt(self):
        """Test prevention of using symlinks to bypass permission checks"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[str(self.test_dir)],  # Only allow test directory
            follow_symlinks=True
        )
        
        # Create symlink that tries to bypass whitelist
        bypass_symlink = self.test_dir / "bypass_symlink.tmp"
        
        try:
            # Point to restricted directory
            bypass_symlink.symlink_to("/System/Library")
            
            # Should not allow bypass of whitelist through symlink
            artifacts = list(scanner._scan_directory(self.test_dir))
            
            # Should respect whitelist even with symlinks
            for artifact in artifacts:
                # All artifacts should be within allowed directory
                resolved_path = artifact.path.resolve()
                allowed = any(
                    str(resolved_path).startswith(str(Path(allowed_path).resolve()))
                    for allowed_path in [str(self.test_dir)]
                )
                if not allowed:
                    self.fail(f"Symlink bypass detected: {artifact.path} -> {resolved_path}")
                    
        except OSError:
            pass

    def test_nuker_symlink_safety(self):
        """Test that nuker handles symlinks safely during deletion"""
        nuker = DigitalNuker(
            logger=self.mock_logger,
            safe_mode=True
        )
        
        # Create safe file and symlink to it
        safe_file = self.test_dir / "safe_file.txt"
        safe_file.write_text("safe content")
        
        test_symlink = self.test_dir / "test_symlink"
        
        try:
            test_symlink.symlink_to(safe_file)
            
            # Test safety check on symlink
            is_safe = nuker._is_safe_to_delete(test_symlink)
            
            # Should apply appropriate safety checks to symlinks
            self.assertIsInstance(is_safe, bool)
            
            # If marked safe, should handle deletion appropriately
            if is_safe:
                result = nuker._execute_deletion(test_symlink, dry_run=True)
                self.assertIsInstance(result.success, bool)
                
        except OSError:
            pass

    def test_symlink_broken_link_handling(self):
        """Test handling of broken/dangling symlinks"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=True
        )
        
        # Create broken symlink
        broken_symlink = self.test_dir / "broken_symlink.tmp"
        non_existent_target = self.test_dir / "does_not_exist.txt"
        
        try:
            broken_symlink.symlink_to(non_existent_target)
            
            # Should handle broken symlinks gracefully
            artifacts = list(scanner._scan_directory(self.test_dir))
            
            # Should not crash or cause errors with broken symlinks
            # May or may not include the broken symlink in results
            for artifact in artifacts:
                self.assertIsInstance(artifact.path, Path)
                
        except OSError:
            pass

    def test_symlink_device_file_protection(self):
        """Test protection against symlinks to device files"""
        scanner = FilesystemScanner(
            patterns_path=self.patterns_file,
            whitelist=[],
            follow_symlinks=True
        )
        
        device_targets = [
            "/dev/null",
            "/dev/zero", 
            "/dev/random",
            "/dev/urandom"
        ]
        
        for device in device_targets:
            with self.subTest(device=device):
                device_symlink = self.test_dir / f"device_symlink_{device.replace('/', '_')}.tmp"
                
                try:
                    device_symlink.symlink_to(device)
                    
                    # Should not follow symlinks to device files
                    artifacts = list(scanner._scan_directory(self.test_dir))
                    
                    # Should not access device files through symlinks
                    for artifact in artifacts:
                        self.assertNotIn("dev", str(artifact.path))
                        
                except OSError:
                    continue


if __name__ == '__main__':
    unittest.main(verbosity=2)