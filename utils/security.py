"""
Security utilities for Cibozer
Provides secure file operations and input validation
"""

import os
import re
from pathlib import Path
from typing import Optional, Union
import secrets
import string


class SecurityError(Exception):
    """Raised when a security violation is detected"""
    pass


def secure_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        A safe filename with dangerous characters removed
        
    Raises:
        SecurityError: If the filename is invalid or dangerous
    """
    if not filename:
        raise SecurityError("Filename cannot be empty")
    
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters but keep extensions
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    filename = filename.strip('-').strip()
    
    # Check if filename is empty after cleaning
    if not filename:
        raise SecurityError("Filename cannot be empty after sanitization")
    
    # Prevent hidden files
    if filename.startswith('.'):
        raise SecurityError("Hidden files are not allowed")
    
    # Prevent double extensions that could bypass filters
    parts = filename.split('.')
    if len(parts) > 2:
        # Keep only the last extension
        filename = f"{'.'.join(parts[:-1]).replace('.', '_')}.{parts[-1]}"
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    # Final validation
    if not filename or filename in ('.', '..'):
        raise SecurityError("Invalid filename")
    
    return filename


def secure_path_join(base_dir: str, *paths: str) -> str:
    """
    Safely join paths preventing directory traversal attacks
    
    Args:
        base_dir: The base directory (must exist)
        *paths: Path components to join
        
    Returns:
        A safe absolute path guaranteed to be within base_dir
        
    Raises:
        SecurityError: If the resulting path would escape base_dir
    """
    # Convert to Path objects for better handling
    base = Path(base_dir).resolve()
    
    # Ensure base directory exists
    if not base.exists():
        raise SecurityError(f"Base directory does not exist: {base_dir}")
    
    # Join and resolve the full path
    full_path = base
    for path_component in paths:
        # Check for absolute paths
        if os.path.isabs(path_component):
            raise SecurityError(f"Absolute paths not allowed: {path_component}")
        
        # Clean each component
        clean_component = secure_filename(path_component)
        full_path = full_path / clean_component
    
    # Resolve to absolute path
    full_path = full_path.resolve()
    
    # Ensure the resolved path is within base_dir
    try:
        full_path.relative_to(base)
    except ValueError:
        raise SecurityError(f"Path traversal attempt detected: {full_path}")
    
    return str(full_path)


def validate_json_filename(filename: str) -> str:
    """
    Validate and sanitize a JSON filename
    
    Args:
        filename: The filename to validate
        
    Returns:
        A safe JSON filename
        
    Raises:
        SecurityError: If the filename is invalid
    """
    if not filename.endswith('.json'):
        raise SecurityError("Filename must end with .json")
    
    return secure_filename(filename)


def validate_video_filename(filename: str) -> str:
    """
    Validate and sanitize a video filename
    
    Args:
        filename: The filename to validate
        
    Returns:
        A safe video filename
        
    Raises:
        SecurityError: If the filename is invalid
    """
    allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        raise SecurityError(f"Invalid video file extension: {ext}")
    
    return secure_filename(filename)


def validate_pdf_filename(filename: str) -> str:
    """
    Validate and sanitize a PDF filename
    
    Args:
        filename: The filename to validate
        
    Returns:
        A safe PDF filename
        
    Raises:
        SecurityError: If the filename is invalid
    """
    if not filename.endswith('.pdf'):
        raise SecurityError("Filename must end with .pdf")
    
    return secure_filename(filename)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token
    
    Args:
        length: Length of the token
        
    Returns:
        A secure random string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def validate_secret_key(secret_key: str) -> bool:
    """
    Validate that a secret key meets security requirements
    
    Args:
        secret_key: The secret key to validate
        
    Returns:
        True if the secret key is strong enough
    """
    if not secret_key:
        return False
    
    # Minimum length requirement
    if len(secret_key) < 32:
        return False
    
    # Check for common weak patterns
    weak_patterns = [
        'secret', 'password', '12345', 'admin', 'default',
        'changeme', 'test', 'demo', 'example'
    ]
    
    secret_lower = secret_key.lower()
    for pattern in weak_patterns:
        if pattern in secret_lower:
            return False
    
    # Ensure some complexity
    has_upper = any(c.isupper() for c in secret_key)
    has_lower = any(c.islower() for c in secret_key)
    has_digit = any(c.isdigit() for c in secret_key)
    has_special = any(not c.isalnum() for c in secret_key)
    
    complexity = sum([has_upper, has_lower, has_digit, has_special])
    
    return complexity >= 3


def sanitize_user_input(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks
    
    Args:
        input_str: The input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        A sanitized string safe for display
    """
    if not input_str:
        return ""
    
    # Convert to string and limit length
    input_str = str(input_str)[:max_length]
    
    # Remove null bytes
    input_str = input_str.replace('\x00', '')
    
    # Basic HTML escaping
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        "<": "&lt;",
        ">": "&gt;",
        "/": "&#x2F;",
    }
    
    for char, escape in html_escape_table.items():
        input_str = input_str.replace(char, escape)
    
    return input_str.strip()


# Export all security functions
__all__ = [
    'SecurityError',
    'secure_filename',
    'secure_path_join',
    'validate_json_filename',
    'validate_video_filename',
    'validate_pdf_filename',
    'generate_secure_token',
    'validate_secret_key',
    'sanitize_user_input'
]