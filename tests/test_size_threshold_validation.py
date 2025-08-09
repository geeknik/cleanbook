#!/usr/bin/env python3
"""
Size Threshold Validation Security Tests
========================================

Tests to verify that size threshold parsing and validation properly rejects
malicious input and prevents integer overflow attacks. These tests ensure
that the security patches in the parse_size_threshold function work correctly.
"""

import unittest
import sys
import os
import math
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cleanbook import parse_size_threshold


class TestSizeThresholdValidation(unittest.TestCase):
    """Test suite for size threshold validation security"""

    def test_negative_values_rejected(self):
        """Test that negative size values are properly rejected"""
        negative_inputs = [
            "-1MB",
            "-100GB", 
            "-0.5TB",
            "-999KB",
            "-1.5GB"
        ]
        
        for input_value in negative_inputs:
            with self.subTest(input=input_value):
                with self.assertRaises(ValueError) as context:
                    parse_size_threshold(input_value)
                self.assertIn("bounds", str(context.exception).lower())

    def test_excessive_values_rejected(self):
        """Test that excessively large values are rejected"""
        excessive_inputs = [
            "9999999999999999999999MB",  # Way beyond reasonable limits
            "999999999999GB",            # Massive GB value
            "999999999TB",               # Massive TB value
            "1048577MB",                 # Just above 1TB limit
            "2097152MB",                 # 2TB in MB
        ]
        
        for input_value in excessive_inputs:
            with self.subTest(input=input_value):
                with self.assertRaises(ValueError) as context:
                    parse_size_threshold(input_value)
                self.assertIn("bounds", str(context.exception).lower())

    def test_infinity_values_rejected(self):
        """Test that infinity values are properly rejected"""
        infinity_inputs = [
            "infMB",
            "infinityGB",
            "1.7976931348623157e+308MB",  # Close to float max
            "1e400MB",                    # Way beyond float range
        ]
        
        for input_value in infinity_inputs:
            with self.subTest(input=input_value):
                with self.assertRaises(ValueError):
                    parse_size_threshold(input_value)

    def test_nan_values_rejected(self):
        """Test that NaN values are properly rejected"""
        nan_inputs = [
            "nanMB",
            "NANMB",
            "NaNGB",
        ]
        
        for input_value in nan_inputs:
            with self.subTest(input=input_value):
                with self.assertRaises(ValueError):
                    parse_size_threshold(input_value)

    def test_malformed_input_rejected(self):
        """Test that malformed input strings are rejected"""
        malformed_inputs = [
            "",           # Empty string
            "MB",         # No numeric value
            "abc123MB",   # Invalid characters
            "12.34.56MB", # Multiple decimal points
            "12..34MB",   # Double decimal points
            "12,34MB",    # Comma instead of decimal
            "12 34MB",    # Space in number
            "12.MB",      # Trailing decimal
            ".12MB",      # Leading decimal only
        ]
        
        for input_value in malformed_inputs:
            with self.subTest(input=input_value):
                with self.assertRaises(ValueError):
                    parse_size_threshold(input_value)

    def test_injection_attempts_rejected(self):
        """Test that code injection attempts in size strings are rejected"""
        injection_inputs = [
            "1MB; rm -rf /",
            "1MB && echo 'injected'",
            "1MB | cat /etc/passwd",
            "1MB $(echo vulnerable)",
            "1MB `echo vulnerable`",
            "1MB</dev/null",
            "1MB>output.txt",
            "1MB\necho injected",
            "1MB\recho injected",
            "1MB\techo injected",
        ]
        
        for input_value in injection_inputs:
            with self.subTest(input=input_value):
                with self.assertRaises(ValueError):
                    parse_size_threshold(input_value)

    def test_unicode_attack_rejected(self):
        """Test that unicode-based attacks are rejected"""
        unicode_inputs = [
            "1МB",     # Cyrillic М instead of M
            "1МВ",     # Cyrillic МВ instead of MB  
            "1ＭＢ",    # Full-width characters
            "1\u202eMB", # Right-to-left override
            "1\u0000MB", # Null byte
        ]
        
        for input_value in unicode_inputs:
            with self.subTest(input=input_value):
                with self.assertRaises(ValueError):
                    parse_size_threshold(input_value)

    def test_scientific_notation_edge_cases(self):
        """Test edge cases with scientific notation"""
        scientific_inputs = [
            "1e100MB",    # Very large exponent
            "1e-100MB",   # Very small exponent  
            "1.0e+308MB", # Near float overflow
            "1.0e-324MB", # Near float underflow
        ]
        
        for input_value in scientific_inputs:
            with self.subTest(input=input_value):
                with self.assertRaises(ValueError):
                    parse_size_threshold(input_value)

    def test_valid_inputs_accepted(self):
        """Test that valid, reasonable inputs are accepted"""
        valid_inputs = [
            ("1MB", 1.0),
            ("100MB", 100.0),
            ("1GB", 1024.0),
            ("2GB", 2048.0),
            ("1TB", 1048576.0),
            ("0.5GB", 512.0),
            ("1.5GB", 1536.0),
            ("500KB", 0.48828125),  # 500/1024
            ("1024KB", 1.0),
            ("0MB", 0.0),
            ("1", 1.0),  # No unit, defaults to MB
            ("100", 100.0),
        ]
        
        for input_value, expected in valid_inputs:
            with self.subTest(input=input_value):
                result = parse_size_threshold(input_value)
                self.assertAlmostEqual(result, expected, places=5)

    def test_boundary_values(self):
        """Test boundary values at the limits of acceptable range"""
        boundary_inputs = [
            ("0MB", 0.0),           # Minimum valid value
            ("1048576MB", 1048576.0), # Maximum valid value (1TB)
        ]
        
        for input_value, expected in boundary_inputs:
            with self.subTest(input=input_value):
                result = parse_size_threshold(input_value)
                self.assertAlmostEqual(result, expected, places=2)

    def test_case_insensitive_units(self):
        """Test that unit parsing is case insensitive"""
        case_variations = [
            ("100mb", 100.0),
            ("100MB", 100.0),
            ("100Mb", 100.0),
            ("100mB", 100.0),
            ("1gb", 1024.0),
            ("1GB", 1024.0),
            ("1Gb", 1024.0),
            ("1gB", 1024.0),
            ("1tb", 1048576.0),
            ("1TB", 1048576.0),
            ("1kb", 1.0/1024),
            ("1KB", 1.0/1024),
        ]
        
        for input_value, expected in case_variations:
            with self.subTest(input=input_value):
                result = parse_size_threshold(input_value)
                self.assertAlmostEqual(result, expected, places=5)

    def test_whitespace_handling(self):
        """Test handling of whitespace in input"""
        whitespace_inputs = [
            " 100MB ",  # Leading/trailing spaces
            "100 MB",   # Space before unit
            " 100 MB ", # Spaces everywhere
            "100MB\n",  # Trailing newline
            "100MB\r",  # Trailing carriage return
            "100MB\t",  # Trailing tab
        ]
        
        for input_value in whitespace_inputs:
            with self.subTest(input=input_value):
                # Should either be handled gracefully or rejected
                try:
                    result = parse_size_threshold(input_value)
                    # If accepted, should be the correct value
                    self.assertAlmostEqual(result, 100.0, places=2)
                except ValueError:
                    # Rejection is also acceptable for whitespace-containing input
                    pass

    def test_input_sanitization(self):
        """Test that input sanitization removes dangerous characters"""
        # Test that sanitization is working by checking internal behavior
        sanitized_inputs = [
            ("100!@#$%^&*()MB", 100.0),  # Special characters removed
            ("100[]{}MB", 100.0),        # Brackets removed
            ("100<>MB", 100.0),          # Angle brackets removed
            ("100\"'MB", 100.0),         # Quotes removed
        ]
        
        for input_value, expected in sanitized_inputs:
            with self.subTest(input=input_value):
                try:
                    result = parse_size_threshold(input_value)
                    # If sanitization works, should get correct value
                    self.assertAlmostEqual(result, expected, places=2)
                except ValueError:
                    # Strict rejection is also acceptable
                    pass

    def test_type_validation(self):
        """Test that non-string inputs are rejected"""
        invalid_types = [
            123,        # Integer
            123.45,     # Float
            None,       # None
            [],         # List
            {},         # Dict
            True,       # Boolean
            b"100MB",   # Bytes
        ]
        
        for input_value in invalid_types:
            with self.subTest(input=str(type(input_value))):
                with self.assertRaises(ValueError):
                    parse_size_threshold(input_value)

    def test_empty_and_none_input(self):
        """Test handling of empty and None input"""
        empty_inputs = [None, "", "   "]
        
        for input_value in empty_inputs:
            with self.subTest(input=repr(input_value)):
                if input_value is None:
                    # Should handle None gracefully
                    result = parse_size_threshold(input_value)
                    self.assertEqual(result, 0.0)
                else:
                    # Empty strings should raise ValueError
                    with self.assertRaises(ValueError):
                        parse_size_threshold(input_value)

    def test_precision_handling(self):
        """Test that floating point precision is handled correctly"""
        precision_inputs = [
            ("1.1MB", 1.1),
            ("1.01MB", 1.01),
            ("1.001MB", 1.001),
            ("1.0001MB", 1.0001),
            ("99.99MB", 99.99),
            ("0.1MB", 0.1),
            ("0.01MB", 0.01),
        ]
        
        for input_value, expected in precision_inputs:
            with self.subTest(input=input_value):
                result = parse_size_threshold(input_value)
                self.assertAlmostEqual(result, expected, places=4)

    def test_regex_sanitization_security(self):
        """Test that regex-based sanitization doesn't introduce vulnerabilities"""
        # Test edge cases in the regex sanitization
        regex_edge_cases = [
            "1.[0-9]*MB",    # Regex-like pattern
            "1.{1,3}MB",     # Regex quantifier
            "1.+MB",         # Regex plus
            "1.*MB",         # Regex star
            "1.^MB",         # Regex anchor
            "1.$MB",         # Regex anchor
            "1.\\MB",        # Backslash
            "1.|MB",         # Regex OR
        ]
        
        for input_value in regex_edge_cases:
            with self.subTest(input=input_value):
                with self.assertRaises(ValueError):
                    parse_size_threshold(input_value)


if __name__ == '__main__':
    unittest.main(verbosity=2)