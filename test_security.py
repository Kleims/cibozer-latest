"""
Tests for security utilities
"""

import pytest
import os
import tempfile
from pathlib import Path
from utils.security import (
    SecurityError, secure_filename, secure_path_join,
    validate_json_filename, validate_video_filename, validate_pdf_filename,
    generate_secure_token, validate_secret_key, sanitize_user_input
)


class TestSecureFilename:
    """Test secure filename sanitization"""
    
    def test_valid_filenames(self):
        """Test that valid filenames pass through"""
        assert secure_filename("test.txt") == "test.txt"
        assert secure_filename("my-file_123.json") == "my-file_123.json"
        assert secure_filename("report 2024.pdf") == "report-2024.pdf"
    
    def test_path_traversal_attempts(self):
        """Test that path traversal attempts are blocked"""
        assert secure_filename("../../../etc/passwd") == "passwd"
        assert secure_filename("..\\..\\windows\\system32\\config") == "config"
        assert secure_filename("/etc/passwd") == "passwd"
    
    def test_dangerous_characters(self):
        """Test removal of dangerous characters"""
        assert secure_filename("file<script>.txt") == "filescript.txt"
        assert secure_filename("file|name.txt") == "filename.txt"
        assert secure_filename("file:name.txt") == "filename.txt"
    
    def test_hidden_files_blocked(self):
        """Test that hidden files are rejected"""
        with pytest.raises(SecurityError):
            secure_filename(".hidden")
        with pytest.raises(SecurityError):
            secure_filename(".env")
    
    def test_double_extensions(self):
        """Test handling of double extensions"""
        assert secure_filename("file.txt.exe") == "file_txt.exe"
        assert secure_filename("report.pdf.js") == "report_pdf.js"
    
    def test_empty_filename(self):
        """Test that empty filenames are rejected"""
        with pytest.raises(SecurityError):
            secure_filename("")
        with pytest.raises(SecurityError):
            secure_filename("   ")
    
    def test_special_filenames(self):
        """Test that special filenames are rejected"""
        with pytest.raises(SecurityError):
            secure_filename(".")
        with pytest.raises(SecurityError):
            secure_filename("..")


class TestSecurePathJoin:
    """Test secure path joining"""
    
    def test_valid_path_join(self, tmp_path):
        """Test joining valid paths"""
        base = str(tmp_path)
        result = secure_path_join(base, "subdir", "file.txt")
        assert result == str(tmp_path / "subdir" / "file.txt")
    
    def test_path_traversal_blocked(self, tmp_path):
        """Test that path traversal is blocked"""
        base = str(tmp_path)
        with pytest.raises(SecurityError):
            secure_path_join(base, "..", "etc", "passwd")
        with pytest.raises(SecurityError):
            secure_path_join(base, "subdir", "..", "..", "etc")
    
    def test_absolute_path_blocked(self, tmp_path):
        """Test that absolute paths are blocked"""
        base = str(tmp_path)
        with pytest.raises(SecurityError):
            secure_path_join(base, "/etc/passwd")
        with pytest.raises(SecurityError):
            secure_path_join(base, "C:\\Windows\\System32")
    
    def test_nonexistent_base(self):
        """Test that nonexistent base directory is rejected"""
        with pytest.raises(SecurityError):
            secure_path_join("/nonexistent/path", "file.txt")


class TestFileValidators:
    """Test file type validators"""
    
    def test_json_validator(self):
        """Test JSON filename validation"""
        assert validate_json_filename("data.json") == "data.json"
        assert validate_json_filename("my-report_123.json") == "my-report_123.json"
        
        with pytest.raises(SecurityError):
            validate_json_filename("data.txt")
        with pytest.raises(SecurityError):
            validate_json_filename("data.json.exe")
    
    def test_video_validator(self):
        """Test video filename validation"""
        assert validate_video_filename("video.mp4") == "video.mp4"
        assert validate_video_filename("clip.avi") == "clip.avi"
        assert validate_video_filename("movie.MOV") == "movie.MOV"
        
        with pytest.raises(SecurityError):
            validate_video_filename("video.txt")
        with pytest.raises(SecurityError):
            validate_video_filename("video.exe")
    
    def test_pdf_validator(self):
        """Test PDF filename validation"""
        assert validate_pdf_filename("report.pdf") == "report.pdf"
        assert validate_pdf_filename("meal-plan_2024.pdf") == "meal-plan_2024.pdf"
        
        with pytest.raises(SecurityError):
            validate_pdf_filename("report.txt")
        with pytest.raises(SecurityError):
            validate_pdf_filename("report.pdf.exe")


class TestSecretKeyValidation:
    """Test secret key strength validation"""
    
    def test_strong_keys(self):
        """Test that strong keys pass validation"""
        assert validate_secret_key("Th1s!sAv3ryStr0ng&S3cur3K3y#2024")
        assert validate_secret_key("a" * 32 + "B1!")  # Minimum length with complexity
    
    def test_weak_keys(self):
        """Test that weak keys fail validation"""
        assert not validate_secret_key("")
        assert not validate_secret_key("short")
        assert not validate_secret_key("a" * 31)  # Too short
        assert not validate_secret_key("password123456789012345678901234")  # Contains 'password'
        assert not validate_secret_key("secretkey123456789012345678901234")  # Contains 'secret'
        assert not validate_secret_key("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")  # No complexity
    
    def test_common_patterns_blocked(self):
        """Test that common weak patterns are blocked"""
        weak_patterns = ['secret', 'password', '12345', 'admin', 'default', 'changeme', 'test', 'demo']
        for pattern in weak_patterns:
            key = pattern + "X" * (32 - len(pattern))
            assert not validate_secret_key(key)


class TestSecureToken:
    """Test secure token generation"""
    
    def test_token_length(self):
        """Test token has correct length"""
        token = generate_secure_token(32)
        assert len(token) == 32
        
        token = generate_secure_token(64)
        assert len(token) == 64
    
    def test_token_uniqueness(self):
        """Test that tokens are unique"""
        tokens = set()
        for _ in range(100):
            token = generate_secure_token(32)
            assert token not in tokens
            tokens.add(token)
    
    def test_token_characters(self):
        """Test token contains only alphanumeric characters"""
        token = generate_secure_token(100)
        assert all(c.isalnum() for c in token)


class TestInputSanitization:
    """Test user input sanitization"""
    
    def test_html_escaping(self):
        """Test HTML characters are escaped"""
        assert sanitize_user_input("<script>alert('xss')</script>") == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;&#x2F;script&gt;"
        assert sanitize_user_input('"quoted"') == "&quot;quoted&quot;"
        assert sanitize_user_input("O'Brien") == "O&#x27;Brien"
    
    def test_null_byte_removal(self):
        """Test null bytes are removed"""
        assert sanitize_user_input("test\x00string") == "teststring"
        assert sanitize_user_input("\x00start") == "start"
    
    def test_length_limiting(self):
        """Test input length is limited"""
        long_input = "a" * 2000
        assert len(sanitize_user_input(long_input)) == 1000
        assert len(sanitize_user_input(long_input, max_length=50)) == 50
    
    def test_empty_input(self):
        """Test empty input handling"""
        assert sanitize_user_input("") == ""
        assert sanitize_user_input(None) == ""
        assert sanitize_user_input("   ") == ""


if __name__ == '__main__':
    pytest.main([__file__, '-v'])