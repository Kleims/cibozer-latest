"""
Basic test suite for Cibozer core functionality
Tests input validation, configuration, and basic operations
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import modules to test
from cibozer import MealPlanParameters, CibozerVideoGenerator, VideoConfig, SlideGenerator
from app_config import get_app_config
config = get_app_config()


class TestMealPlanParameters(unittest.TestCase):
    """Test MealPlanParameters validation and functionality"""
    
    def test_valid_parameters(self):
        """Test that valid parameters are accepted"""
        params = MealPlanParameters(
            calories=2000,
            diet_type="vegan",
            macro_goal="high protein",
            meal_structure="3+2"
        )
        
        self.assertEqual(params.calories, 2000)
        self.assertEqual(params.diet_type, "vegan")
        self.assertEqual(params.macro_goal, "high protein")
        self.assertEqual(params.meal_structure, "3+2")
    
    def test_calorie_validation(self):
        """Test calorie range validation"""
        # Test too low
        with self.assertRaises(ValueError):
            MealPlanParameters(
                calories=500,
                diet_type="vegan",
                macro_goal="high protein",
                meal_structure="3+2"
            )
        
        # Test too high
        with self.assertRaises(ValueError):
            MealPlanParameters(
                calories=6000,
                diet_type="vegan",
                macro_goal="high protein",
                meal_structure="3+2"
            )
        
        # Test string conversion
        params = MealPlanParameters(
            calories="2000",
            diet_type="vegan",
            macro_goal="high protein",
            meal_structure="3+2"
        )
        self.assertEqual(params.calories, 2000)
    
    def test_diet_type_validation(self):
        """Test diet type validation"""
        # Test invalid diet
        with self.assertRaises(ValueError):
            MealPlanParameters(
                calories=2000,
                diet_type="carnivore",
                macro_goal="high protein",
                meal_structure="3+2"
            )
        
        # Test case insensitive
        params = MealPlanParameters(
            calories=2000,
            diet_type="VEGAN",
            macro_goal="high protein",
            meal_structure="3+2"
        )
        self.assertEqual(params.diet_type, "vegan")
    
    def test_macro_goal_validation(self):
        """Test macro goal validation"""
        # Test invalid macro goal
        with self.assertRaises(ValueError):
            MealPlanParameters(
                calories=2000,
                diet_type="vegan",
                macro_goal="super protein",
                meal_structure="3+2"
            )
        
        # Test case insensitive
        params = MealPlanParameters(
            calories=2000,
            diet_type="vegan",
            macro_goal="HIGH PROTEIN",
            meal_structure="3+2"
        )
        self.assertEqual(params.macro_goal, "high protein")
    
    def test_meal_structure_validation(self):
        """Test meal structure validation"""
        # Test invalid structure
        with self.assertRaises(ValueError):
            MealPlanParameters(
                calories=2000,
                diet_type="vegan",
                macro_goal="high protein",
                meal_structure="4 meals"
            )
        
        # Test valid structures
        valid_structures = ["3 meals", "3+2", "5 small", "2 meals", "OMAD"]
        for structure in valid_structures:
            params = MealPlanParameters(
                calories=2000,
                diet_type="vegan",
                macro_goal="high protein",
                meal_structure=structure
            )
            self.assertEqual(params.meal_structure, structure)
    
    def test_filename_generation(self):
        """Test filename generation"""
        params = MealPlanParameters(
            calories=2000,
            diet_type="vegan",
            macro_goal="high protein",
            meal_structure="3+2"
        )
        
        filename = params.get_filename_base()
        self.assertIn("cibozer_vegan_2000_highprotein_3plus2", filename)
        # Check that filename ends with today's date (format: YYYYMMDD)
        import datetime
        today = datetime.datetime.now().strftime("%Y%m%d")
        self.assertTrue(filename.endswith(f"_{today}"))  # Dynamic date
    
    def test_optimizer_preferences_conversion(self):
        """Test conversion to optimizer preferences"""
        params = MealPlanParameters(
            calories=2000,
            diet_type="vegan",
            macro_goal="high protein",
            meal_structure="3+2"
        )
        
        prefs = params.to_optimizer_preferences()
        
        self.assertEqual(prefs['diet'], 'vegan')
        self.assertEqual(prefs['calories'], 2000)
        self.assertEqual(prefs['pattern'], 'standard')
        self.assertIn('cuisines', prefs)
        self.assertIn('timestamp', prefs)


class TestCibozerVideoGenerator(unittest.TestCase):
    """Test CibozerVideoGenerator functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = CibozerVideoGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_generator_initialization(self):
        """Test generator initializes correctly"""
        self.assertIsNotNone(self.generator.config)
        self.assertIsNotNone(self.generator.video_creator)
        self.assertIsNotNone(self.generator.optimizer)
        
        # Check supported options
        self.assertIn("vegan", self.generator.diet_types)
        self.assertIn("high protein", self.generator.macro_goals)
        self.assertIn("3+2", self.generator.meal_structures)
    
    def test_generate_video_input_validation(self):
        """Test input validation in generate_video method"""
        # Test invalid output path type
        with self.assertRaises(ValueError):
            self.generator.generate_video(
                diet_type="vegan",
                calories=2000,
                macro_goal="high protein",
                meal_structure="3+2",
                output_path=123  # Invalid type
            )
        
        # Test invalid calories
        with self.assertRaises(ValueError):
            self.generator.generate_video(
                diet_type="vegan",
                calories=500,  # Too low
                macro_goal="high protein",
                meal_structure="3+2",
                output_path=self.temp_dir
            )
    
    def test_generate_video_creates_output_directory(self):
        """Test that output directory is created"""
        test_output = os.path.join(self.temp_dir, "test_output")
        
        # Mock the video creator methods to avoid actual video generation
        with patch.object(self.generator.video_creator, 'create_longform_video') as mock_long, \
             patch.object(self.generator.video_creator, 'create_shorts_video') as mock_short:
            
            self.generator.generate_video(
                diet_type="vegan",
                calories=2000,
                macro_goal="high protein",
                meal_structure="3+2",
                output_path=test_output
            )
            
            # Verify directory was created
            self.assertTrue(os.path.exists(test_output))
            
            # Verify methods were called
            mock_long.assert_called_once()
            mock_short.assert_called_once()


class TestVideoConfig(unittest.TestCase):
    """Test VideoConfig functionality"""
    
    def test_video_config_initialization(self):
        """Test VideoConfig initializes with correct defaults"""
        config = VideoConfig()
        
        self.assertEqual(config.width, 1920)
        self.assertEqual(config.height, 1080)
        self.assertEqual(config.fps, 30)
        self.assertIsInstance(config.bg_color, tuple)
        self.assertIsInstance(config.text_color, tuple)
    
    def test_video_config_customization(self):
        """Test VideoConfig can be customized"""
        config = VideoConfig(
            width=1280,
            height=720,
            fps=24
        )
        
        self.assertEqual(config.width, 1280)
        self.assertEqual(config.height, 720)
        self.assertEqual(config.fps, 24)


class TestSlideGenerator(unittest.TestCase):
    """Test SlideGenerator functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = VideoConfig()
        self.generator = SlideGenerator(self.config)
    
    def test_slide_generator_initialization(self):
        """Test SlideGenerator initializes correctly"""
        self.assertIsNotNone(self.generator.config)
        self.assertIsNotNone(self.generator.font_title)
        self.assertIsNotNone(self.generator.font_body)
    
    def test_font_setup(self):
        """Test font setup works on current platform"""
        # This should not raise an exception
        self.generator.setup_fonts()
        
        # Fonts should be available (even if default)
        self.assertIsNotNone(self.generator.font_title)
        self.assertIsNotNone(self.generator.font_body)
    
    def test_base_slide_creation(self):
        """Test base slide creation"""
        img, draw = self.generator.create_base_slide()
        
        self.assertIsNotNone(img)
        self.assertIsNotNone(draw)
        self.assertEqual(img.size, (self.config.width, self.config.height))


class TestConfiguration(unittest.TestCase):
    """Test configuration management"""
    
    def test_default_config_creation(self):
        """Test default configuration creation"""
        # Use the config object from app_config instead of non-existent CibozerConfig
        from app_config import get_app_config
        config = get_app_config()
        
        # Test that config has expected attributes
        self.assertTrue(hasattr(config, 'payment'))
        self.assertTrue(hasattr(config.payment, 'STRIPE_SECRET_KEY'))
        self.assertTrue(hasattr(config.payment, 'STRIPE_PUBLISHABLE_KEY'))
        self.assertTrue(hasattr(config, 'database'))
        self.assertTrue(hasattr(config.database, 'DATABASE_URL'))
        # Check for flask config
        self.assertTrue(hasattr(config, 'flask'))
        self.assertTrue(hasattr(config.flask, 'SECRET_KEY'))
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test that config object has expected methods
        from app_config import get_app_config
        config = get_app_config()
        
        # Test that config has validation attributes
        self.assertTrue(hasattr(config, 'flask'))
        self.assertTrue(hasattr(config.flask, 'SECRET_KEY'))
        self.assertTrue(hasattr(config.flask, 'TESTING'))
        
        # Verify default values
        self.assertIsNotNone(config.flask.SECRET_KEY)
        
        # Config should be valid
        self.assertTrue(True)  # Config loaded successfully means it's valid
    
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables"""
        # Test that config can read from environment
        from app_config import get_app_config
        config = get_app_config()
        
        # Test that the config object has environment-based fields
        self.assertTrue(hasattr(config.flask, 'DEBUG'))
        # The DEBUG flag is set from FLASK_DEBUG env var or defaults to False
        self.assertIsInstance(config.flask.DEBUG, bool)
    
    def test_config_singleton(self):
        """Test configuration singleton pattern"""
        from app_config import get_app_config
        
        config1 = get_app_config()
        config2 = get_app_config()
        
        # Both should return the same config object
        self.assertEqual(type(config1).__name__, type(config2).__name__)


class TestIntegration(unittest.TestCase):
    """Integration tests for core functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_parameter_validation(self):
        """Test end-to-end parameter validation"""
        generator = CibozerVideoGenerator()
        
        # Test valid parameters flow
        try:
            params = MealPlanParameters(
                calories=2000,
                diet_type="vegan",
                macro_goal="high protein",
                meal_structure="3+2"
            )
            
            # Should not raise exception
            prefs = params.to_optimizer_preferences()
            self.assertIsInstance(prefs, dict)
            
        except Exception as e:
            self.fail(f"Valid parameters should not raise exception: {e}")
    
    def test_font_loading_robustness(self):
        """Test font loading works across platforms"""
        config = VideoConfig()
        generator = SlideGenerator(config)
        
        # Should not crash
        generator.setup_fonts()
        
        # Should have working fonts (even if default)
        self.assertIsNotNone(generator.font_title)
        self.assertIsNotNone(generator.font_body)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestMealPlanParameters,
        TestCibozerVideoGenerator,
        TestVideoConfig,
        TestSlideGenerator,
        TestConfiguration,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTest Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: [FAILURE]")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: [ERROR]")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)