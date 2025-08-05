"""Secure file handling utilities"""
import os
import hashlib
import magic
from pathlib import Path
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_type(file_path):
    """Validate file type using python-magic"""
    file_mime = magic.from_file(file_path, mime=True)
    allowed_mimes = {
        'application/pdf',
        'image/png',
        'image/jpeg',
        'image/gif'
    }
    return file_mime in allowed_mimes

def secure_file_path(base_path, filename):
    """Generate secure file path preventing directory traversal"""
    # Ensure filename is secure
    filename = secure_filename(filename)
    
    # Generate unique filename to prevent overwrites
    name, ext = os.path.splitext(filename)
    unique_name = f"{name}_{hashlib.md5(os.urandom(16)).hexdigest()}{ext}"
    
    # Ensure path doesn't escape base directory
    file_path = Path(base_path) / unique_name
    file_path = file_path.resolve()
    base_path = Path(base_path).resolve()
    
    if not str(file_path).startswith(str(base_path)):
        raise ValueError("Invalid file path")
    
    return file_path

def scan_file_for_malware(file_path):
    """Scan file for potential malware (implement with ClamAV or similar)"""
    # This is a placeholder - in production, integrate with antivirus
    # For now, just check for suspicious patterns
    
    suspicious_patterns = [
        b'<%eval',
        b'<%execute',
        b'\x00<script',
        b'javascript:',
        b'onerror='
    ]
    
    with open(file_path, 'rb') as f:
        content = f.read(1024 * 100)  # Read first 100KB
        
    for pattern in suspicious_patterns:
        if pattern in content.lower():
            return False
    
    return True

def cleanup_old_files(directory, max_age_days=7):
    """Clean up old temporary files"""
    import time
    
    directory = Path(directory)
    now = time.time()
    
    for file_path in directory.iterdir():
        if file_path.is_file():
            file_age = now - file_path.stat().st_mtime
            if file_age > (max_age_days * 24 * 3600):
                try:
                    file_path.unlink()
                except:
                    pass  # Log error in production
