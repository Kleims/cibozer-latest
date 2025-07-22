"""
Web-safe wrapper for MealOptimizer
Prevents interactive input() calls from crashing the web application
"""

import sys
import io
from contextlib import contextmanager
from meal_optimizer import MealPlanOptimizer as _MealPlanOptimizer

class WebSafeMealOptimizer(_MealPlanOptimizer):
    """
    Web-safe version of MealPlanOptimizer that redirects stdin
    to prevent input() calls from blocking the web server
    """
    
    def __init__(self):
        # Temporarily redirect stdin during initialization
        # to handle any potential input() calls
        old_stdin = sys.stdin
        sys.stdin = io.StringIO('')
        try:
            # Skip validation for web performance - use skip_validation=True
            super().__init__(skip_validation=True)
        except EOFError:
            # If there are input() calls, they'll raise EOFError
            # Initialize with minimal setup
            self._safe_init()
        finally:
            sys.stdin = old_stdin
    
    def _safe_init(self):
        """Minimal initialization without interactive prompts"""
        # Initialize essential attributes without calling parent __init__
        self.templates = getattr(self, 'templates', {})
        self.ingredients = getattr(self, 'ingredients', {})
        self.diet_profiles = getattr(self, 'diet_profiles', {})
        self.meal_patterns = getattr(self, 'meal_patterns', {})
        self.optimization_steps = []
        self.convergence_history = []
        self.algorithm_metrics = {}
        self.logger = None
    
    def __getattribute__(self, name):
        """Override attribute access to wrap methods that might use input()"""
        attr = super().__getattribute__(name)
        
        # List of methods known to use input()
        interactive_methods = [
            'get_user_preferences',
            '_get_choice',
            '_get_restrictions',
            'interactive_setup'
        ]
        
        if callable(attr) and name in interactive_methods:
            def safe_wrapper(*args, **kwargs):
                # Return sensible defaults instead of prompting
                if name == 'get_user_preferences':
                    return {
                        'diet': 'standard',
                        'calories': 2000,
                        'pattern': 'standard',
                        'restrictions': [],
                        'cuisines': ['all'],
                        'cooking_methods': ['all'],
                        'allow_substitutions': True
                    }
                elif name == '_get_choice':
                    # Return first option as default
                    return args[1][0] if len(args) > 1 and args[1] else None
                elif name == '_get_restrictions':
                    return []  # No restrictions by default
                else:
                    # For any other interactive method, return None
                    return None
            
            return safe_wrapper
        
        return attr

# Create a singleton instance for the web app
web_optimizer = None

def get_web_optimizer():
    """Get or create the web-safe optimizer instance"""
    global web_optimizer
    if web_optimizer is None:
        web_optimizer = WebSafeMealOptimizer()
    return web_optimizer