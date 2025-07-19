"""
Enhanced logging system for meal planner with comprehensive event tracking
and improved visual formatting
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path

class MealPlanLogger:
    """Comprehensive logging system for meal planning events"""
    
    def __init__(self, log_level=logging.INFO):
        """Initialize the meal plan logger"""
        self.start_time = time.time()
        self.events = []
        
        # Setup logging directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create custom logger
        self.logger = logging.getLogger('meal_planner')
        self.logger.setLevel(log_level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler for detailed logs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(
            log_dir / f"meal_planner_{timestamp}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for formatted output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)8s | %(funcName)20s:%(lineno)3d | %(message)s'
        )
        console_formatter = logging.Formatter('%(message)s')
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_event(self, event_type: str, message: str, data: Optional[Dict] = None):
        """Log an event with timestamp and optional data"""
        timestamp = time.time()
        elapsed = timestamp - self.start_time
        
        event = {
            'timestamp': timestamp,
            'elapsed': elapsed,
            'type': event_type,
            'message': message,
            'data': data or {}
        }
        
        self.events.append(event)
        
        # Log to file
        log_msg = f"[{event_type.upper():>12}] {message}"
        if data:
            log_msg += f" | Data: {json.dumps(data, default=str)}"
        
        self.logger.debug(log_msg)
    
    def start_generation(self, preferences: Dict):
        """Log start of meal plan generation"""
        self.log_event("START", "Meal plan generation started", preferences)
        
        print("\n" + "="*80)
        print("CIBOZER MEAL PLANNER - ENHANCED LOGGING")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Target: {preferences.get('calories', 0)} calories")
        print(f"Diet: {preferences.get('diet', 'unknown').title()}")
        print(f"Pattern: {preferences.get('pattern', 'unknown').title()}")
        print("-"*80)
    
    def log_meal_generation(self, meal_name: str, attempt: int, status: str, details: Dict = None):
        """Log meal generation attempt"""
        self.log_event("MEAL_GEN", f"{meal_name} generation attempt {attempt}: {status}", details)
        
        if status == "SUCCESS":
            calories = details.get('calories', 0) if details else 0
            protein = details.get('protein', 0) if details else 0
            print(f"OK {meal_name.upper():>10}: {calories:>5.0f} cal, {protein:>4.1f}g protein")
        elif status == "RETRY":
            reason = details.get('reason', 'unknown') if details else 'unknown'
            print(f"RETRY {meal_name.upper():>10}: Retry #{attempt} ({reason})")
        else:
            error = details.get('error', 'unknown') if details else 'unknown'
            print(f"FAIL {meal_name.upper():>10}: Failed - {error}")
    
    def log_optimization_step(self, step: int, current_accuracy: float, target_accuracy: float):
        """Log optimization step"""
        self.log_event("OPTIMIZE", f"Step {step}: {current_accuracy:.1f}% accuracy", {
            'step': step,
            'current_accuracy': current_accuracy,
            'target_accuracy': target_accuracy
        })
        
        progress_bar = self.create_progress_bar(current_accuracy, target_accuracy)
        print(f"OPT Step {step:>2}: {current_accuracy:>5.1f}% {progress_bar}")
    
    def log_ingredient_substitution(self, original: str, substitute: str, reason: str):
        """Log ingredient substitution"""
        self.log_event("SUBSTITUTE", f"Substituted {original} → {substitute}", {
            'original': original,
            'substitute': substitute,
            'reason': reason
        })
        
        print(f"SUB: {original} -> {substitute} ({reason})")
    
    def log_nutrition_calculation(self, meal_name: str, nutrition: Dict):
        """Log nutrition calculation for a meal"""
        self.log_event("NUTRITION", f"Calculated nutrition for {meal_name}", nutrition)
        
        # Only log to file to avoid console spam
        self.logger.debug(f"Nutrition calculated for {meal_name}: {nutrition}")
    
    def log_constraint_violation(self, constraint: str, current: float, target: float):
        """Log when a constraint is violated"""
        self.log_event("CONSTRAINT", f"Constraint violation: {constraint}", {
            'constraint': constraint,
            'current': current,
            'target': target,
            'deviation': abs(current - target)
        })
        
        deviation = abs(current - target)
        print(f"⚠️  Constraint: {constraint} deviation: {deviation:.1f} (current: {current:.1f}, target: {target:.1f})")
    
    def log_template_selection(self, meal_name: str, template_id: str, score: float):
        """Log template selection"""
        self.log_event("TEMPLATE", f"Selected template {template_id} for {meal_name}", {
            'meal_name': meal_name,
            'template_id': template_id,
            'score': score
        })
        
        # Only log to file to reduce console noise
        self.logger.debug(f"Template selected for {meal_name}: {template_id} (score: {score:.2f})")
    
    def display_final_results(self, meal_plan: Dict, totals: Dict, accuracy: float):
        """Display beautifully formatted final results"""
        self.log_event("COMPLETE", "Meal plan generation completed", {
            'accuracy': accuracy,
            'totals': totals
        })
        
        print("\n" + "="*80)
        print("MEAL PLAN RESULTS")
        print("="*80)
        
        # Overall totals
        print(f"\nDAILY TOTALS:")
        print(f"   Calories: {totals.get('calories', 0):>8.1f}")
        print(f"   Protein:  {totals.get('protein', 0):>8.1f}g")
        print(f"   Carbs:    {totals.get('carbs', 0):>8.1f}g") 
        print(f"   Fat:      {totals.get('fat', 0):>8.1f}g")
        if 'fiber' in totals and totals['fiber'] is not None:
            print(f"   Fiber:    {totals.get('fiber', 0):>8.1f}g")
        print(f"\n   Accuracy: {accuracy:>8.1f}%")
        
        # Meal breakdown
        print(f"\nMEAL BREAKDOWN:")
        print("-"*80)
        
        for meal_name, meal_data in meal_plan.items():
            if isinstance(meal_data, dict) and 'calories' in meal_data:
                print(f"\n{meal_name.upper()}")
                print(f"   {meal_data.get('calories', 0):>6.1f} Cal")
                print(f"   {meal_data.get('protein', 0):>6.1f}g Protein") 
                print(f"   {meal_data.get('carbs', 0):>6.1f}g Carbs")
                print(f"   {meal_data.get('fat', 0):>6.1f}g Fat")
                
                fiber_val = meal_data.get('fiber')
                if fiber_val is not None:
                    print(f"   {fiber_val:>6.1f}g Fiber")
                else:
                    print(f"   {'N/A':>6}g Fiber")
                
                print("   Ingredients:")
                ingredients = meal_data.get('ingredients', [])
                for ing in ingredients[:5]:  # Show first 5 ingredients
                    item = ing.get('item', '').replace('_', ' ').title()
                    amount = ing.get('amount', 0)
                    unit = ing.get('unit', 'g')
                    print(f"     {item}: {amount:.1f}{unit}")
                
                if len(ingredients) > 5:
                    print(f"     ... and {len(ingredients) - 5} more ingredients")
                
                instructions = meal_data.get('instructions', 'No instructions available')
                if instructions and instructions != 'No instructions available':
                    print(f"   Instructions: {instructions[:100]}...")
        
        # Generation stats
        elapsed = time.time() - self.start_time
        print(f"\nGENERATION STATS:")
        print(f"   Time elapsed: {elapsed:.2f}s")
        print(f"   Events logged: {len(self.events)}")
        print(f"   Final accuracy: {accuracy:.1f}%")
        
        print("\n" + "="*80)
        print("MEAL PLAN GENERATION COMPLETE")
        print("="*80 + "\n")
    
    def create_progress_bar(self, current: float, target: float, width: int = 20) -> str:
        """Create a visual progress bar"""
        progress = min(current / target, 1.0) if target > 0 else 0
        filled = int(progress * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {progress*100:.0f}%"
    
    def save_event_log(self, filename: Optional[str] = None):
        """Save detailed event log to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/meal_planner_events_{timestamp}.json"
        
        log_data = {
            'session_start': self.start_time,
            'session_duration': time.time() - self.start_time,
            'total_events': len(self.events),
            'events': self.events
        }
        
        os.makedirs('logs', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        print(f"Detailed event log saved to: {filename}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of the generation process"""
        total_time = time.time() - self.start_time
        
        event_counts = {}
        for event in self.events:
            event_type = event['type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'total_duration': total_time,
            'total_events': len(self.events),
            'event_breakdown': event_counts,
            'avg_time_per_event': total_time / len(self.events) if self.events else 0
        }

# Convenience function for easy integration
def create_logger(log_level=logging.INFO) -> MealPlanLogger:
    """Create a new meal plan logger instance"""
    return MealPlanLogger(log_level)