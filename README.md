# Cibozer - AI-Powered Meal Planning Video Generator

**Cibozer** is an advanced Python application that generates AI-optimized meal plans and creates professional video content for YouTube. It combines sophisticated nutrition optimization algorithms with automated video generation to create engaging meal planning content.

## 🚀 Features

### Core Functionality
- **AI-Powered Meal Optimization**: Uses constraint-solving algorithms to create nutritionally balanced meal plans
- **Video Generation**: Creates both long-form and YouTube Shorts videos automatically
- **Cross-Platform Compatibility**: Works on Windows, macOS, and Linux
- **Multiple Diet Support**: Omnivore, vegetarian, vegan, pescatarian, keto, paleo, and more
- **Flexible Meal Structures**: 3 meals, 3+2 (meals + snacks), 5 small meals, 2 meals, OMAD

### Advanced Features
- **Real-Time Optimization Visualization**: Shows algorithm convergence in generated videos
- **Comprehensive Nutrition Database**: 250+ ingredients with complete nutritional profiles
- **YouTube Metadata Generation**: Auto-generates titles, descriptions, tags, and timestamps
- **Shopping List Generation**: Creates organized shopping lists with quantity optimization
- **Batch Processing**: Generate multiple meal plans and videos efficiently

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Windows 10/11, macOS 10.14+, or Linux

### Dependencies
- OpenCV (cv2) - Video processing
- PIL (Pillow) - Image manipulation
- matplotlib - Chart generation
- numpy - Mathematical operations
- All dependencies are listed in `requirements.txt`

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd cibozer
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python -c "from cibozer import CibozerVideoGenerator; print('Installation successful!')"
```

## 🎯 Quick Start

### Basic Usage
```python
from cibozer import CibozerVideoGenerator

# Initialize generator
generator = CibozerVideoGenerator()

# Generate meal plan videos
generator.generate_video(
    diet_type="vegan",
    calories=2000,
    macro_goal="high protein",
    meal_structure="3+2",
    output_path="./output"
)
```

### Command Line Usage
```bash
# Generate single video
python cibozer.py

# Batch generation
python batch_generator.py
```

## 📊 API Reference

### MealPlanParameters
```python
MealPlanParameters(
    calories: int,           # 800-5000 (recommended: 1200-3500)
    diet_type: str,          # See supported diets below
    macro_goal: str,         # See macro goals below
    meal_structure: str      # See meal structures below
)
```

### Supported Options

#### Diet Types
- `omnivore` - Standard omnivorous diet
- `vegetarian` - Lacto-ovo vegetarian
- `vegan` - Plant-based only
- `pescatarian` - Fish and plant-based
- `keto` - Ketogenic (high fat, low carb)
- `low-carb` - Reduced carbohydrate intake
- `paleo` - Paleolithic diet principles
- `gluten-free` - Gluten-free options

#### Macro Goals
- `balanced` - Balanced macronutrient distribution
- `high protein` - Protein-focused (40/30/30)
- `high carb` - Carbohydrate-focused for athletes
- `keto ratios` - Ketogenic ratios (70/25/5)
- `mediterranean` - Mediterranean diet principles
- `low fat` - Reduced fat intake

#### Meal Structures
- `3 meals` - Traditional breakfast, lunch, dinner
- `3+2` - 3 meals + 2 snacks
- `5 small` - 5 smaller meals throughout the day
- `2 meals` - Intermittent fasting (16:8)
- `OMAD` - One meal a day

## 🎥 Video Output

### Generated Files
For each meal plan, Cibozer generates:
- **Long-form video** (2-3 minutes) - Complete meal plan walkthrough
- **YouTube Shorts** (30 seconds) - Condensed highlight reel
- **Metadata file** - YouTube-ready title, description, tags, timestamps
- **Meal plan JSON** - Complete nutritional data and recipes
- **Shopping list** - Organized by category with quantities

### Video Structure
1. **Introduction** - Diet type and calorie overview
2. **Week Overview** - 7-day meal plan at a glance
3. **Daily Breakdowns** - Detailed meal information
4. **Nutrition Analysis** - Charts and optimization metrics
5. **Shopping List** - Organized ingredient list

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:
```env
# Video Settings
VIDEO_QUALITY=1080p
VIDEO_FPS=30
FONT_SIZE_SCALE=1.0

# Output Settings
DEFAULT_OUTPUT_PATH=./cibozer_output
GENERATE_SHORTS=true
GENERATE_METADATA=true
```

### Customization
- **Colors**: Modify `VideoConfig` class in `cibozer.py`
- **Fonts**: System fonts are auto-detected, or specify custom paths
- **Video Duration**: Adjust slide timings in video generation methods

## 🚨 Error Handling

### Common Issues

#### Font Loading Errors
```
[WARNING] No system fonts found, using default fonts
```
**Solution**: Install system fonts or specify custom font paths

#### Low Calorie Warning
```
[WARNING] Very low calorie count (1000). Consider 1200+ for most adults.
```
**Solution**: Use recommended calorie ranges for safety

#### Invalid Parameters
```
[ERROR] Invalid diet type: carnivore. Valid options: omnivore, vegetarian, vegan...
```
**Solution**: Use only supported diet types (see API reference)

### Input Validation
All inputs are automatically validated with helpful error messages:
- Calorie range: 800-5000 (warnings for extremes)
- Diet compatibility checks
- Meal structure appropriateness
- File path validation

## 🎨 Customization

### Adding New Diets
1. Update `valid_diets` in `MealPlanParameters._validate_diet_type()`
2. Add diet mapping in `to_optimizer_preferences()`
3. Update meal templates in `nutrition_data.py`

### Custom Video Styles
1. Modify `VideoConfig` class for colors and fonts
2. Update slide generation methods in `SlideGenerator`
3. Adjust video timing in `VideoCreator`

## 📈 Performance

### Optimization Features
- **Constraint Solving**: Advanced algorithms for nutritional optimization
- **Caching**: Ingredient and template caching for faster generation
- **Parallel Processing**: Batch generation support
- **Memory Management**: Efficient handling of large nutrition databases

### Benchmarks
- Single meal plan generation: ~30 seconds
- Video creation: ~2-3 minutes
- Batch processing: ~20 meal plans/hour

## 🧪 Testing

### Running Tests
```bash
# Run basic validation tests
python -c "
from cibozer import MealPlanParameters
# Test suite runs automatically during import
"

# Test video generation
python -c "
from cibozer import CibozerVideoGenerator
generator = CibozerVideoGenerator()
print('All systems operational')
"
```

### Manual Testing
1. Generate test meal plan
2. Verify video output quality
3. Check metadata accuracy
4. Validate shopping list

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Run tests before submitting

### Code Style
- Follow PEP 8 guidelines
- Add type hints for new functions
- Include docstrings for all public methods
- Validate inputs in user-facing functions

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Nutrition Database**: Comprehensive ingredient nutritional profiles
- **Optimization Algorithms**: Advanced constraint satisfaction methods
- **Video Generation**: Professional-quality automated video creation
- **Cross-Platform Support**: Robust font and file system handling

## 📞 Support

### Getting Help
- Check the README for common issues
- Review error messages for specific guidance
- Test with minimal examples first

### Common Solutions
1. **Font issues**: Ensure system fonts are installed
2. **Video errors**: Check output directory permissions
3. **Memory issues**: Reduce batch size or video quality
4. **Invalid inputs**: Use provided validation messages

---

**Happy meal planning!** 🍽️

*Generated with automated documentation tools and manual curation for accuracy.*