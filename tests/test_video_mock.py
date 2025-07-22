"""Mock video generation components for testing to avoid OpenCV dependency issues."""

from unittest.mock import MagicMock
import sys


class MockCV2:
    """Mock cv2 module to prevent import errors during testing."""
    
    class VideoWriter:
        def __init__(self, *args, **kwargs):
            pass
        
        def write(self, frame):
            pass
        
        def release(self):
            pass
    
    class dnn:
        DictValue = None
    
    @staticmethod
    def imread(*args, **kwargs):
        # Return a mock image array
        return [[255, 255, 255]]
    
    @staticmethod
    def imwrite(*args, **kwargs):
        return True
    
    @staticmethod
    def VideoCapture(*args, **kwargs):
        mock_cap = MagicMock()
        mock_cap.read.return_value = (True, [[255, 255, 255]])
        mock_cap.release.return_value = None
        return mock_cap


def mock_video_dependencies():
    """Mock video-related dependencies for testing."""
    # Mock cv2 
    if 'cv2' not in sys.modules:
        sys.modules['cv2'] = MockCV2()
    
    # Mock other video dependencies
    mock_modules = [
        'edge_tts',
        'matplotlib.pyplot',
        'PIL.Image',
        'PIL.ImageDraw', 
        'PIL.ImageFont'
    ]
    
    for module in mock_modules:
        if module not in sys.modules:
            sys.modules[module] = MagicMock()


# Auto-apply mocking when this module is imported
mock_video_dependencies()