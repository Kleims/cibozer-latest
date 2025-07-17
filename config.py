"""
Configuration management for Cibozer
Handles environment variables, defaults, and validation
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class CibozerConfig:
    """Main configuration class for Cibozer application"""
    
    # Video Settings
    video_width: int = 1920
    video_height: int = 1080
    video_fps: int = 30
    video_quality: str = "1080p"
    
    # Output Settings
    default_output_path: str = "./cibozer_output"
    generate_shorts: bool = True
    generate_metadata: bool = True
    save_meal_plans: bool = True
    
    # Font Settings
    font_size_scale: float = 1.0
    font_family_preference: str = "arial"
    
    # Performance Settings
    max_batch_size: int = 50
    enable_caching: bool = True
    parallel_processing: bool = True
    
    # Safety Settings
    min_calories: int = 800
    max_calories: int = 5000
    warn_calories_low: int = 1200
    warn_calories_high: int = 3500
    
    # Optimization Settings
    max_iterations: int = 25
    accuracy_target: float = 0.95
    calorie_tolerance: int = 50
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration values"""
        # Video settings
        if self.video_width <= 0 or self.video_height <= 0:
            raise ValueError("Video dimensions must be positive")
        
        if self.video_fps <= 0 or self.video_fps > 60:
            raise ValueError("Video FPS must be between 1 and 60")
        
        # Calorie limits
        if self.min_calories >= self.max_calories:
            raise ValueError("Min calories must be less than max calories")
        
        # Ensure output directory exists
        Path(self.default_output_path).mkdir(parents=True, exist_ok=True)


def load_config() -> CibozerConfig:
    """Load configuration from environment variables with defaults"""
    
    config_dict = {
        # Video Settings
        'video_width': int(os.getenv('CIBOZER_VIDEO_WIDTH', '1920')),
        'video_height': int(os.getenv('CIBOZER_VIDEO_HEIGHT', '1080')),
        'video_fps': int(os.getenv('CIBOZER_VIDEO_FPS', '30')),
        'video_quality': os.getenv('CIBOZER_VIDEO_QUALITY', '1080p'),
        
        # Output Settings
        'default_output_path': os.getenv('CIBOZER_OUTPUT_PATH', './cibozer_output'),
        'generate_shorts': os.getenv('CIBOZER_GENERATE_SHORTS', 'true').lower() == 'true',
        'generate_metadata': os.getenv('CIBOZER_GENERATE_METADATA', 'true').lower() == 'true',
        'save_meal_plans': os.getenv('CIBOZER_SAVE_MEAL_PLANS', 'true').lower() == 'true',
        
        # Font Settings
        'font_size_scale': float(os.getenv('CIBOZER_FONT_SIZE_SCALE', '1.0')),
        'font_family_preference': os.getenv('CIBOZER_FONT_FAMILY', 'arial'),
        
        # Performance Settings
        'max_batch_size': int(os.getenv('CIBOZER_MAX_BATCH_SIZE', '50')),
        'enable_caching': os.getenv('CIBOZER_ENABLE_CACHING', 'true').lower() == 'true',
        'parallel_processing': os.getenv('CIBOZER_PARALLEL_PROCESSING', 'true').lower() == 'true',
        
        # Safety Settings
        'min_calories': int(os.getenv('CIBOZER_MIN_CALORIES', '800')),
        'max_calories': int(os.getenv('CIBOZER_MAX_CALORIES', '5000')),
        'warn_calories_low': int(os.getenv('CIBOZER_WARN_CALORIES_LOW', '1200')),
        'warn_calories_high': int(os.getenv('CIBOZER_WARN_CALORIES_HIGH', '3500')),
        
        # Optimization Settings
        'max_iterations': int(os.getenv('CIBOZER_MAX_ITERATIONS', '25')),
        'accuracy_target': float(os.getenv('CIBOZER_ACCURACY_TARGET', '0.95')),
        'calorie_tolerance': int(os.getenv('CIBOZER_CALORIE_TOLERANCE', '50')),
    }
    
    try:
        return CibozerConfig(**config_dict)
    except (ValueError, TypeError) as e:
        print(f"[ERROR] Configuration error: {e}")
        print("Using default configuration...")
        return CibozerConfig()


def save_config_template(filename: str = ".env.template") -> None:
    """Save a template configuration file"""
    
    template = """# Cibozer Configuration Template
# Copy this file to .env and modify as needed

# Video Settings
CIBOZER_VIDEO_WIDTH=1920
CIBOZER_VIDEO_HEIGHT=1080
CIBOZER_VIDEO_FPS=30
CIBOZER_VIDEO_QUALITY=1080p

# Output Settings
CIBOZER_OUTPUT_PATH=./cibozer_output
CIBOZER_GENERATE_SHORTS=true
CIBOZER_GENERATE_METADATA=true
CIBOZER_SAVE_MEAL_PLANS=true

# Font Settings
CIBOZER_FONT_SIZE_SCALE=1.0
CIBOZER_FONT_FAMILY=arial

# Performance Settings
CIBOZER_MAX_BATCH_SIZE=50
CIBOZER_ENABLE_CACHING=true
CIBOZER_PARALLEL_PROCESSING=true

# Safety Settings
CIBOZER_MIN_CALORIES=800
CIBOZER_MAX_CALORIES=5000
CIBOZER_WARN_CALORIES_LOW=1200
CIBOZER_WARN_CALORIES_HIGH=3500

# Optimization Settings
CIBOZER_MAX_ITERATIONS=25
CIBOZER_ACCURACY_TARGET=0.95
CIBOZER_CALORIE_TOLERANCE=50
"""
    
    with open(filename, 'w') as f:
        f.write(template)
    
    print(f"Configuration template saved to: {filename}")


def print_config_info(config: CibozerConfig) -> None:
    """Print current configuration information"""
    print("\nCurrent Cibozer Configuration:")
    print("=" * 40)
    print(f"Video: {config.video_width}x{config.video_height} @ {config.video_fps}fps")
    print(f"Output: {config.default_output_path}")
    print(f"Shorts: {'Enabled' if config.generate_shorts else 'Disabled'}")
    print(f"Metadata: {'Enabled' if config.generate_metadata else 'Disabled'}")
    print(f"Calorie Range: {config.min_calories}-{config.max_calories}")
    print(f"Batch Size: {config.max_batch_size}")
    print(f"Caching: {'Enabled' if config.enable_caching else 'Disabled'}")


# Global configuration instance
_config: Optional[CibozerConfig] = None

def get_config() -> CibozerConfig:
    """Get global configuration instance (singleton pattern)"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> CibozerConfig:
    """Reload configuration from environment"""
    global _config
    _config = load_config()
    return _config


if __name__ == "__main__":
    # Generate config template when run directly
    save_config_template()
    
    # Show current config
    config = get_config()
    print_config_info(config)