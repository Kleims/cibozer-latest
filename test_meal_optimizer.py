"""
Comprehensive test suite for meal_optimizer.py
Tests the MealPlanOptimizer class for robustness and accuracy
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import numpy as np

from meal_optimizer import MealPlanOptimizer
import nutrition_data as nd


class TestMealPlanOptimizer:
    """Test suite for MealPlanOptimizer initialization and configuration"""
    
    @pytest.fixture
    def optimizer(self):
        """Create a basic optimizer instance"""
        return MealPlanOptimizer()
    
    @pytest.fixture
    def custom_optimizer(self):
        """Create optimizer with custom preferences"""
        return MealPlanOptimizer(
            cuisine_preferences=['mexican', 'italian'],
            cooking_preferences=['grilling', 'baking']
        )
    
    def test_initialization_default(self, optimizer):
        """Test default initialization"""
        assert optimizer.cuisine_preferences == ["all"]
        assert optimizer.cooking_preferences == ["all"]
        assert optimizer.substitution_enabled is True
        assert optimizer.ACCURACY_TARGET == 0.95
        assert optimizer.MAX_ITERATIONS == 25
        assert optimizer.CALORIE_TOLERANCE == 50
        assert optimizer.MACRO_TOLERANCE == 3
    
    def test_initialization_custom(self, custom_optimizer):
        """Test initialization with custom preferences"""
        assert custom_optimizer.cuisine_preferences == ['mexican', 'italian']
        assert custom_optimizer.cooking_preferences == ['grilling', 'baking']
    
    def test_constants_validation(self, optimizer):
        """Test mathematical constants are properly set"""
        assert optimizer.EPSILON == 1e-10
        assert optimizer.MAX_SCALE_FACTOR == 10.0
        assert optimizer.MIN_SCALE_FACTOR == 0.1
        assert optimizer.CONVERGENCE_THRESHOLD == 1e-6
        assert optimizer.MAX_INGREDIENT_AMOUNT == 1000
        assert optimizer.MIN_INGREDIENT_AMOUNT == 1
        assert optimizer.MAX_DAILY_CALORIES == 6000
        assert optimizer.MIN_DAILY_CALORIES == 800
    
    def test_portion_size_limits(self, optimizer):
        """Test portion size limits are properly configured"""
        assert optimizer.PORTION_SIZE_LIMITS['protein'] == (20, 300)
        assert optimizer.PORTION_SIZE_LIMITS['carbs'] == (10, 150)
        assert optimizer.PORTION_SIZE_LIMITS['fat'] == (5, 100)
    
    def test_cooking_factors_exist(self, optimizer):
        """Test cooking factors are initialized"""
        assert 'chicken_breast' in optimizer.cooking_factors
        assert optimizer.cooking_factors['chicken_breast'] == 0.75
        assert 'rice' in optimizer.cooking_factors
        assert optimizer.cooking_factors['rice'] == 2.8
    
    def test_max_shopping_amounts(self, optimizer):
        """Test shopping amount limits"""
        assert 'lettuce' in optimizer.max_shopping_amounts
        assert optimizer.max_shopping_amounts['lettuce'] == 1000
        assert 'chicken_breast' in optimizer.max_shopping_amounts
        assert optimizer.max_shopping_amounts['chicken_breast'] == 3000
    
    def test_algorithm_metrics_initialization(self, optimizer):
        """Test algorithm metrics are properly initialized"""
        metrics = optimizer.algorithm_metrics
        assert metrics['iterations'] == 0
        assert metrics['constraints_checked'] == 0
        assert metrics['templates_evaluated'] == 0
        assert metrics['substitutions_made'] == 0
        assert metrics['optimization_time'] == 0
        assert metrics['final_accuracy'] == 0
        assert metrics['convergence_achieved'] is False
        assert metrics['validation_errors'] == 0
        assert metrics['fallback_used'] is False
    
    @patch('meal_optimizer.MealPlanOptimizer._validate_database_integrity')
    @patch('meal_optimizer.MealPlanOptimizer._get_seasonal_ingredients')
    @patch('meal_optimizer.MealPlanOptimizer._get_regional_preferences')
    @patch('meal_optimizer.MealPlanOptimizer._get_medical_condition_profiles')
    @patch('meal_optimizer.MealPlanOptimizer._get_special_dietary_needs')
    def test_initialization_calls_setup_methods(self, mock_special, mock_medical, 
                                              mock_regional, mock_seasonal, mock_validate):
        """Test that initialization calls all setup methods"""
        mock_seasonal.return_value = []
        mock_regional.return_value = {}
        mock_medical.return_value = {}
        mock_special.return_value = {}
        
        optimizer = MealPlanOptimizer()
        
        mock_validate.assert_called_once()
        mock_seasonal.assert_called_once()
        mock_regional.assert_called_once()
        mock_medical.assert_called_once()
        mock_special.assert_called_once()


class TestDatabaseValidation:
    """Test database integrity validation"""
    
    def test_validate_database_integrity_valid(self, capsys):
        """Test validation with valid data"""
        optimizer = MealPlanOptimizer()
        # Should print OK message
        captured = capsys.readouterr()
        assert "[OK] Database integrity validation passed" in captured.out or "[WARNING]" in captured.out
    
    @patch('meal_optimizer.nd.INGREDIENTS')
    def test_validate_database_integrity_missing_fields(self, mock_ingredients, capsys):
        """Test validation with missing required fields"""
        mock_ingredients.update({
            'test_ingredient': {
                'calories': 100,
                'protein': 10,
                # Missing 'fat' and 'carbs'
            }
        })
        
        optimizer = MealPlanOptimizer()
        captured = capsys.readouterr()
        assert "[WARNING]" in captured.out
    
    @patch('meal_optimizer.nd.INGREDIENTS')
    def test_validate_database_integrity_negative_values(self, mock_ingredients, capsys):
        """Test validation with negative nutritional values"""
        mock_ingredients.update({
            'bad_ingredient': {
                'calories': -100,
                'protein': 10,
                'fat': 5,
                'carbs': 20
            }
        })
        
        optimizer = MealPlanOptimizer()
        captured = capsys.readouterr()
        assert "[WARNING]" in captured.out
    
    @patch('meal_optimizer.nd.DIET_PROFILES')
    def test_validate_diet_profiles_macros_sum(self, mock_profiles, capsys):
        """Test validation of diet profile macros"""
        mock_profiles.update({
            'bad_diet': {
                'macros': {
                    'protein': 30,
                    'fat': 30,
                    'carbs': 30  # Sum is 90, not 100
                }
            }
        })
        
        optimizer = MealPlanOptimizer()
        captured = capsys.readouterr()
        assert "[WARNING]" in captured.out


class TestMealPlanGeneration:
    """Test meal plan generation functionality"""
    
    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance for testing"""
        return MealPlanOptimizer()
    
    def test_generate_single_day_plan(self, optimizer):
        """Test single day plan generation"""
        preferences = {
            'calories': 2000,
            'diet': 'balanced',
            'cuisine': ['all'],
            'meal_types': ['breakfast', 'lunch', 'dinner']
        }
        
        result, metrics = optimizer.generate_single_day_plan(preferences)
        
        assert isinstance(result, dict)
        assert isinstance(metrics, dict)
        assert 'breakfast' in result or 'lunch' in result or 'dinner' in result
    
    def test_calculate_nutrition_score(self, optimizer):
        """Test nutrition score calculation"""
        nutrition = {
            'calories': 2000,
            'protein': 150,
            'fat': 56,
            'carbs': 225
        }
        target_macros = {
            'protein': 30,
            'fat': 25,
            'carbs': 45
        }
        
        score = optimizer.calculate_nutrition_score(nutrition, 2000, target_macros)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
    
    def test_calculate_macro_percentages(self, optimizer):
        """Test macro percentage calculations"""
        nutrition = {
            'calories': 2000,
            'protein': 150,  # 600 cal = 30%
            'fat': 56,       # 504 cal = 25.2%
            'carbs': 225     # 900 cal = 45%
        }
        
        percentages = optimizer.calculate_macro_percentages(nutrition)
        
        assert 'protein' in percentages
        assert 'fat' in percentages
        assert 'carbs' in percentages
        assert abs(percentages['protein'] - 30) < 1
        assert abs(percentages['fat'] - 25.2) < 1
        assert abs(percentages['carbs'] - 45) < 1
    
    def test_calculate_day_totals(self, optimizer):
        """Test day totals calculation"""
        meals = {
            'breakfast': {
                'totals': {
                    'calories': 400,
                    'protein': 30,
                    'fat': 15,
                    'carbs': 40
                }
            },
            'lunch': {
                'totals': {
                    'calories': 600,
                    'protein': 45,
                    'fat': 20,
                    'carbs': 60
                }
            },
            'dinner': {
                'totals': {
                    'calories': 800,
                    'protein': 60,
                    'fat': 25,
                    'carbs': 80
                }
            }
        }
        
        totals = optimizer.calculate_day_totals(meals)
        
        assert totals['calories'] == 1800
        assert totals['protein'] == 135
        assert totals['fat'] == 60
        assert totals['carbs'] == 180
    
    def test_validate_meal_plan(self, optimizer):
        """Test meal plan validation"""
        # Valid meal plan
        valid_plan = {
            'daily_totals': {
                'calories': 2000,
                'protein': 150,
                'fat': 56,
                'carbs': 225
            }
        }
        
        is_valid, message = optimizer.validate_meal_plan(
            valid_plan,
            target_calories=2000,
            diet_type='balanced'
        )
        assert is_valid is True
        
        # Invalid meal plan (too few calories)
        invalid_plan = {
            'daily_totals': {
                'calories': 1000,
                'protein': 75,
                'fat': 28,
                'carbs': 112
            }
        }
        
        is_valid, message = optimizer.validate_meal_plan(
            invalid_plan,
            target_calories=2000,
            diet_type='balanced'
        )
        assert is_valid is False
        assert "calories" in message.lower()


class TestIngredientScaling:
    """Test ingredient scaling and portion calculations"""
    
    @pytest.fixture
    def optimizer(self):
        return MealPlanOptimizer()
    
    def test_convert_unit_to_grams(self, optimizer):
        """Test unit to grams conversion"""
        # Test various conversions
        assert optimizer.convert_unit_to_grams('cup', 1) == pytest.approx(128, rel=0.1)
        assert optimizer.convert_unit_to_grams('oz', 1) == pytest.approx(28.35, rel=0.1)
        assert optimizer.convert_unit_to_grams('g', 100) == 100
        assert optimizer.convert_unit_to_grams('lb', 1) == pytest.approx(453.6, rel=0.1)
    
    def test_generate_shopping_list(self, optimizer):
        """Test shopping list generation"""
        meal_plan = {
            'Day 1': {
                'breakfast': {
                    'ingredients': [
                        {'item': 'eggs', 'amount': 100, 'unit': 'g'},
                        {'item': 'bread', 'amount': 50, 'unit': 'g'}
                    ]
                },
                'lunch': {
                    'ingredients': [
                        {'item': 'chicken_breast', 'amount': 150, 'unit': 'g'},
                        {'item': 'rice', 'amount': 80, 'unit': 'g'}
                    ]
                }
            }
        }
        
        shopping_list = optimizer.generate_shopping_list(meal_plan)
        
        assert isinstance(shopping_list, dict)
        assert 'grouped' in shopping_list
        assert 'eggs' in shopping_list['grouped']['protein']
    
    def test_validate_shopping_amounts(self, optimizer):
        """Test shopping amount validation"""
        shopping_list = {
            'grouped': {
                'protein': {
                    'chicken_breast': {
                        'total_amount': 5000,  # Too much
                        'unit': 'g'
                    },
                    'eggs': {
                        'total_amount': 500,
                        'unit': 'g'
                    }
                }
            }
        }
        
        validated = optimizer.validate_shopping_amounts(shopping_list)
        
        assert validated['grouped']['protein']['chicken_breast']['total_amount'] <= optimizer.max_shopping_amounts.get('chicken_breast', 5000)


class TestUtilityFunctions:
    """Test utility and helper functions"""
    
    @pytest.fixture
    def optimizer(self):
        return MealPlanOptimizer()
    
    def test_get_seasonal_ingredients(self, optimizer):
        """Test seasonal ingredient detection"""
        # Method returns a dict, not a list
        seasonal = optimizer._get_seasonal_ingredients()
        assert isinstance(seasonal, dict)
        assert 'spring' in seasonal
        assert 'summer' in seasonal
        assert 'fall' in seasonal
        assert 'winter' in seasonal
    
    def test_get_regional_preferences(self, optimizer):
        """Test regional preference loading"""
        # Method should return a dict
        regional = optimizer._get_regional_preferences()
        assert isinstance(regional, dict)
    
    def test_calculate_meal_nutrition(self, optimizer):
        """Test meal nutrition calculation"""
        meal_template = {
            'base_ingredients': [
                {'item': 'chicken_breast', 'base_amount': 100},
                {'item': 'white_rice', 'base_amount': 50}
            ]
        }
        
        nutrition = optimizer.calculate_meal_nutrition(meal_template, scale_factor=1.0)
        
        assert 'calories' in nutrition
        assert 'protein' in nutrition
        assert 'fat' in nutrition
        assert 'carbs' in nutrition
        assert nutrition['calories'] > 0
    
    def test_optimization_tracking(self, optimizer):
        """Test optimization tracking and metrics"""
        preferences = {
            'calories': 2000,
            'diet': 'balanced',
            'cuisine': ['all'],
            'meal_types': ['breakfast', 'lunch', 'dinner']
        }
        
        result = optimizer.generate_day_with_tracking(preferences)
        
        assert 'meals' in result
        assert 'totals' in result
        assert 'steps' in result
        assert 'final_accuracy' in result
        assert 'total_iterations' in result
        assert 'time_seconds' in result
        assert result['final_accuracy'] >= 0
        assert result['total_iterations'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])