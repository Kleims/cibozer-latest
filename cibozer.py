# cibozer.py - Enhanced with week overviews and YouTube metadata generation

import os
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from meal_optimizer import MealPlanOptimizer
import nutrition_data as nd

# Configuration
@dataclass
class VideoConfig:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    font_size_title: int = 72
    font_size_body: int = 48
    font_size_medium: int = 42
    font_size_small: int = 36
    font_size_tiny: int = 28
    font_size_micro: int = 24
    bg_color: tuple = (13, 19, 23)  # Dark background
    text_color: tuple = (255, 255, 255)  # White text
    accent_color: tuple = (13, 115, 119)  # Teal
    highlight_color: tuple = (255, 107, 53)  # Orange
    success_color: tuple = (39, 174, 96)  # Green
    error_color: tuple = (231, 76, 60)  # Red
    secondary_color: tuple = (52, 73, 94)  # Dark blue
    gradient_color: tuple = (46, 64, 87)  # Gradient blue

@dataclass
class MealPlanParameters:
    calories: int
    diet_type: str
    macro_goal: str
    meal_structure: str
    
    def __post_init__(self):
        """Validate parameters after initialization"""
        self._validate_calories()
        self._validate_diet_type()
        self._validate_macro_goal()
        self._validate_meal_structure()
    
    def _validate_calories(self):
        """Validate calorie input"""
        if not isinstance(self.calories, int):
            try:
                self.calories = int(self.calories)
            except (ValueError, TypeError):
                raise ValueError(f"Calories must be a number, got: {self.calories}")
        
        if self.calories < 800:
            raise ValueError(f"Calories too low ({self.calories}). Minimum is 800 for safety.")
        
        if self.calories > 5000:
            raise ValueError(f"Calories too high ({self.calories}). Maximum is 5000.")
        
        # Warning for extreme values
        if self.calories < 1200:
            print(f"[WARNING] Very low calorie count ({self.calories}). Consider 1200+ for most adults.")
        elif self.calories > 3500:
            print(f"[WARNING] Very high calorie count ({self.calories}). Consider if appropriate.")
    
    def _validate_diet_type(self):
        """Validate diet type"""
        if not isinstance(self.diet_type, str):
            raise ValueError(f"Diet type must be a string, got: {type(self.diet_type)}")
        
        valid_diets = {
            "omnivore", "vegetarian", "vegan", "pescatarian", 
            "keto", "low-carb", "paleo", "gluten-free"
        }
        
        if self.diet_type.lower() not in valid_diets:
            raise ValueError(f"Invalid diet type: {self.diet_type}. Valid options: {', '.join(valid_diets)}")
        
        # Normalize to lowercase
        self.diet_type = self.diet_type.lower()
    
    def _validate_macro_goal(self):
        """Validate macro goal"""
        if not isinstance(self.macro_goal, str):
            raise ValueError(f"Macro goal must be a string, got: {type(self.macro_goal)}")
        
        valid_macros = {
            "high protein", "balanced", "high carb", 
            "keto ratios", "mediterranean", "low fat"
        }
        
        if self.macro_goal.lower() not in valid_macros:
            raise ValueError(f"Invalid macro goal: {self.macro_goal}. Valid options: {', '.join(valid_macros)}")
        
        # Normalize to lowercase
        self.macro_goal = self.macro_goal.lower()
        
        # Check for compatibility
        if self.diet_type in ["keto", "low-carb"] and self.macro_goal not in ["keto ratios", "high protein"]:
            print(f"[WARNING] {self.macro_goal} macro goal may not be optimal for {self.diet_type} diet")
    
    def _validate_meal_structure(self):
        """Validate meal structure"""
        if not isinstance(self.meal_structure, str):
            raise ValueError(f"Meal structure must be a string, got: {type(self.meal_structure)}")
        
        valid_structures = {"3 meals", "3+2", "5 small", "2 meals", "OMAD"}
        
        if self.meal_structure not in valid_structures:
            raise ValueError(f"Invalid meal structure: {self.meal_structure}. Valid options: {', '.join(valid_structures)}")
        
        # Check for compatibility with calories
        if self.meal_structure == "OMAD" and self.calories > 2500:
            print(f"[WARNING] OMAD with {self.calories} calories may be difficult to consume in one meal")
        
        if self.meal_structure == "5 small" and self.calories < 1500:
            print(f"[WARNING] 5 small meals with {self.calories} calories may result in very small portions")
    
    def get_filename_base(self):
        date = datetime.now().strftime("%Y%m%d")
        return f"cibozer_{self.diet_type.lower()}_{self.calories}_{self.macro_goal.lower().replace(' ', '')}_{self.meal_structure.replace(' ', '').replace('+', 'plus')}_{date}"
    
    def to_optimizer_preferences(self):
        """Convert cibozer params to meal optimizer format"""
        # Map diet types
        diet_map = {
            "omnivore": "standard",
            "vegetarian": "vegetarian", 
            "vegan": "vegan",
            "pescatarian": "pescatarian",
            "keto": "keto",
            "low-carb": "keto",
            "paleo": "paleo",
            "gluten-free": "standard"  # with restrictions
        }
        
        # Map meal structures to patterns
        pattern_map = {
            "3 meals": "standard",
            "3+2": "standard",  # 3 meals + 2 snacks
            "5 small": "bodybuilding",
            "2 meals": "18_6_if",
            "OMAD": "omad"
        }
        
        preferences = {
            'diet': diet_map.get(self.diet_type, 'standard'),
            'cuisines': ['all'],
            'cooking_methods': ['all'],
            'pattern': pattern_map.get(self.meal_structure, 'standard'),
            'restrictions': ['gluten'] if self.diet_type == 'gluten-free' else [],
            'calories': self.calories,
            'measurement_system': 'US',
            'allow_substitutions': True,
            'timestamp': datetime.now().isoformat()
        }
        
        return preferences

@dataclass
class YouTubeMetadata:
    """Store YouTube metadata including timestamps"""
    title: str
    description: str
    tags: List[str]
    timestamps: List[Tuple[str, str]]  # (time, description)
    
    def to_string(self) -> str:
        """Generate copy-paste ready YouTube metadata"""
        output = []
        output.append("=== YOUTUBE VIDEO METADATA ===\n")
        output.append(f"TITLE:\n{self.title}\n")
        output.append(f"DESCRIPTION:\n{self.description}\n")
        output.append("TIMESTAMPS:")
        for time, desc in self.timestamps:
            output.append(f"{time} - {desc}")
        output.append("")
        output.append(f"TAGS:\n{', '.join(self.tags)}\n")
        return '\n'.join(output)

class SlideGenerator:
    """Generates individual slides for videos"""
    
    def __init__(self, config: VideoConfig):
        self.config = config
        self.setup_fonts()
    
    def setup_fonts(self):
        """Setup fonts with cross-platform compatibility"""
        import platform
        
        # Define font paths for different platforms
        font_paths = {
            'Windows': [
                'C:/Windows/Fonts/arial.ttf',
                'C:/Windows/Fonts/calibri.ttf',
                'C:/Windows/Fonts/tahoma.ttf',
                'C:/Windows/Fonts/verdana.ttf'
            ],
            'Darwin': [  # macOS
                '/System/Library/Fonts/Arial.ttf',
                '/System/Library/Fonts/Helvetica.ttc',
                '/Library/Fonts/Arial.ttf'
            ],
            'Linux': [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/usr/share/fonts/TTF/DejaVuSans.ttf'
            ]
        }
        
        # Get current platform
        current_platform = platform.system()
        available_fonts = font_paths.get(current_platform, font_paths['Linux'])
        
        # Try to find a working font
        working_font = None
        for font_path in available_fonts:
            try:
                # Test if font loads
                test_font = ImageFont.truetype(font_path, 12)
                working_font = font_path
                break
            except (OSError, IOError):
                continue
        
        if working_font:
            try:
                self.font_path = working_font  # Store for reuse
                self.font_title = ImageFont.truetype(working_font, self.config.font_size_title)
                self.font_body = ImageFont.truetype(working_font, self.config.font_size_body)
                self.font_medium = ImageFont.truetype(working_font, self.config.font_size_medium)
                self.font_small = ImageFont.truetype(working_font, self.config.font_size_small)
                self.font_tiny = ImageFont.truetype(working_font, self.config.font_size_tiny)
                self.font_micro = ImageFont.truetype(working_font, self.config.font_size_micro)
                print(f"[OK] Using font: {working_font}")
            except Exception as e:
                print(f"[WARNING] Font loading error: {e}")
                self._setup_default_fonts()
        else:
            print("[WARNING] No system fonts found, using default fonts")
            self._setup_default_fonts()
    
    def _setup_default_fonts(self):
        """Setup default fonts as fallback"""
        try:
            # Try to get better default fonts
            self.font_title = ImageFont.load_default()
            self.font_body = ImageFont.load_default()  
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_tiny = ImageFont.load_default()
            self.font_micro = ImageFont.load_default()
        except Exception as e:
            print(f"[WARNING] Default font loading error: {e}")
            # Last resort - create minimal font objects
            self.font_title = self.font_body = self.font_medium = None
            self.font_small = self.font_tiny = self.font_micro = None
    
    def create_base_slide(self) -> Tuple[Image.Image, ImageDraw.Draw]:
        """Create base slide with gradient background"""
        img = Image.new('RGB', (self.config.width, self.config.height), self.config.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add subtle gradient
        for i in range(self.config.height):
            gradient_alpha = i / self.config.height
            r = int(self.config.bg_color[0] * (1 - gradient_alpha * 0.2))
            g = int(self.config.bg_color[1] * (1 - gradient_alpha * 0.2))
            b = int(self.config.bg_color[2] * (1 - gradient_alpha * 0.2))
            draw.line([(0, i), (self.config.width, i)], fill=(r, g, b))
        
        return img, draw
    
    def center_text(self, draw, text, y_position, font, color=None):
        """Center text horizontally on slide"""
        if color is None:
            color = self.config.text_color
        
        # Handle None font gracefully
        if font is None:
            font = ImageFont.load_default()
        
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            x_position = (self.config.width - text_width) // 2
            draw.text((x_position, y_position), text, fill=color, font=font)
        except Exception as e:
            print(f"[WARNING] Text rendering error: {e}")
            # Fallback to simple text placement
            draw.text((50, y_position), text, fill=color)
    
    def create_title_slide(self, params: MealPlanParameters) -> Image.Image:
        """Create enhanced title slide for meal plan"""
        img, draw = self.create_base_slide()
        
        # Add decorative elements
        self._add_decorative_corners(draw)
        
        # Main title with better styling
        self.center_text(draw, "14-DAY MEAL PLAN", self.config.height // 3 - 50, self.font_title)
        
        # Subtitle line
        draw.line([(self.config.width // 4, self.config.height // 3 + 20), 
                   (3 * self.config.width // 4, self.config.height // 3 + 20)], 
                  fill=self.config.accent_color, width=3)
        
        # Diet parameters with icons
        param_text = f"{params.diet_type.upper()} DIET"
        self.center_text(draw, param_text, self.config.height // 2 - 50, self.font_body)
        
        cal_text = f"{params.calories} CALORIES DAILY"
        self.center_text(draw, cal_text, self.config.height // 2 + 20, self.font_medium)
        
        macro_text = f"{params.macro_goal.upper()} FOCUS"
        self.center_text(draw, macro_text, self.config.height // 2 + 80, self.font_medium)
        
        # What you'll get section with better formatting
        y_offset = 2 * self.config.height // 3 + 20
        features = [
            "✓ Complete 2-week meal plan",
            "✓ Detailed shopping list",
            "✓ Optimized nutrition daily",
            "✓ Easy meal prep instructions"
        ]
        
        # Feature box background
        box_height = len(features) * 45 + 20
        draw.rectangle([self.config.width // 4 - 20, y_offset - 10, 
                       3 * self.config.width // 4 + 20, y_offset + box_height],
                       fill=(30, 40, 50), outline=self.config.accent_color, width=2)
        
        for i, feature in enumerate(features):
            y_pos = y_offset + i * 45
            bbox = draw.textbbox((0, 0), feature, font=self.font_small)
            text_width = bbox[2] - bbox[0]
            x_position = (self.config.width - text_width) // 2
            draw.text((x_position, y_pos), feature, fill=self.config.success_color, font=self.font_small)
        
        return img
    
    def create_full_week_overview_slide(self, week_num: int, week_data: Dict[str, Dict], 
                                       params: MealPlanParameters) -> Image.Image:
        """Create comprehensive week overview showing all 7 days at once"""
        img, draw = self.create_base_slide()
        
        # Title
        title_text = f"WEEK {week_num} OVERVIEW"
        self.center_text(draw, title_text, 30, self.font_body)
        
        # Week stats summary
        week_totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
        for day_data in week_data.values():
            for key in week_totals:
                week_totals[key] += day_data['totals'][key]
        
        avg_calories = week_totals['calories'] / 7
        cal_accuracy = max(0, 100 - abs(avg_calories - params.calories) / params.calories * 100)
        
        # Stats bar
        stats_text = f"Daily Average: {avg_calories:.0f} cal | Accuracy: {cal_accuracy:.0f}%"
        self.center_text(draw, stats_text, 80, self.font_small, color=(180, 180, 180))
        
        # Create grid layout for 7 days
        grid_start_y = 140
        grid_height = self.config.height - 200
        day_height = grid_height // 7
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day_idx, day_name in enumerate(days):
            if day_name not in week_data:
                continue
                
            day_data = week_data[day_name]
            y_start = grid_start_y + day_idx * day_height
            
            # Day background with alternating colors
            if day_idx % 2 == 0:
                draw.rectangle([40, y_start, self.config.width - 40, y_start + day_height - 5],
                              fill=(25, 35, 45))
            
            # Day header
            draw.rectangle([40, y_start, 200, y_start + 40], 
                          fill=self.config.accent_color)
            draw.text((50, y_start + 8), day_name.upper()[:3], 
                     fill=self.config.text_color, font=self.font_medium)
            
            # Meals summary (horizontally arranged)
            meals = day_data['meals']
            x_offset = 220
            meal_width = (self.config.width - 280) // 4
            
            meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
            for meal_type in meal_types:
                # Find meal of this type
                meal_found = None
                for meal_name, meal_info in meals.items():
                    if meal_type in meal_name.lower():
                        meal_found = meal_info
                        break
                
                if meal_found:
                    # Meal name (abbreviated)
                    meal_display = meal_found['name']
                    if len(meal_display) > 22:
                        meal_display = meal_display[:19] + '...'
                    
                    draw.text((x_offset, y_start + 10), meal_type.capitalize(), 
                             fill=self.config.highlight_color, font=self.font_tiny)
                    draw.text((x_offset, y_start + 35), meal_display, 
                             fill=self.config.text_color, font=self.font_micro)
                    draw.text((x_offset, y_start + 60), f"{meal_found['calories']:.0f} cal", 
                             fill=self.config.success_color, font=self.font_micro)
                
                x_offset += meal_width
            
            # Day totals on the right
            totals = day_data['totals']
            totals_x = self.config.width - 180
            
            # Calorie accuracy indicator
            cal_diff = abs(totals['calories'] - params.calories)
            if cal_diff <= 50:
                accuracy_color = self.config.success_color
            elif cal_diff <= 100:
                accuracy_color = self.config.highlight_color
            else:
                accuracy_color = self.config.error_color
            
            draw.text((totals_x, y_start + 20), f"{totals['calories']:.0f}", 
                     fill=accuracy_color, font=self.font_body)
            draw.text((totals_x, y_start + 65), "calories", 
                     fill=(150, 150, 150), font=self.font_micro)
        
        # Legend at bottom
        legend_y = self.config.height - 40
        draw.text((50, legend_y), "Color coding:", fill=(150, 150, 150), font=self.font_micro)
        
        # Accuracy indicators
        indicators = [
            (self.config.success_color, "Within 50 cal"),
            (self.config.highlight_color, "Within 100 cal"),
            (self.config.error_color, "Over 100 cal")
        ]
        
        x_pos = 200
        for color, label in indicators:
            draw.rectangle([x_pos, legend_y - 5, x_pos + 15, legend_y + 10], fill=color)
            draw.text((x_pos + 20, legend_y), label, fill=(150, 150, 150), font=self.font_micro)
            x_pos += 150
        
        return img
    
    def create_week_overview_slide(self, week_num: int, days_data: Dict[str, Dict], 
                                  days_range: str, params: MealPlanParameters) -> Image.Image:
        """Create clean week overview with split days (e.g., Mon-Thu or Fri-Sun)"""
        img, draw = self.create_base_slide()
        
        # Title
        title_text = f"WEEK {week_num}: {days_range}"
        self.center_text(draw, title_text, 40, self.font_body)
        
        # Subtitle showing diet focus
        subtitle = f"{params.diet_type.title()} Diet - {params.calories} Calorie Target"
        self.center_text(draw, subtitle, 90, self.font_small, color=(180, 180, 180))
        
        # Starting positions
        start_y = 150
        day_column_width = self.config.width // len(days_data)
        
        # Process each day
        for day_idx, (day_name, day_data) in enumerate(days_data.items()):
            x_start = day_idx * day_column_width + 40
            y_pos = start_y
            
            # Day header with colored background
            header_color = self.config.accent_color if day_idx % 2 == 0 else self.config.secondary_color
            draw.rectangle([x_start - 10, y_pos, x_start + day_column_width - 50, y_pos + 45], 
                          fill=header_color)
            
            # Day name
            draw.text((x_start + 20, y_pos + 10), day_name.upper(), 
                     fill=self.config.text_color, font=self.font_medium)
            
            y_pos += 60
            
            # Get meals
            meals = day_data['meals']
            meal_order = ['breakfast', 'lunch', 'dinner', 'snack']
            
            # Show each meal type
            for meal_type in meal_order:
                for meal_name, meal_info in meals.items():
                    if meal_type in meal_name.lower():
                        # Meal type label
                        meal_label = meal_type.capitalize()
                        draw.text((x_start, y_pos), meal_label, 
                                 fill=self.config.highlight_color, font=self.font_tiny)
                        y_pos += 30
                        
                        # Meal name (abbreviated if needed)
                        meal_display = meal_info['name']
                        if len(meal_display) > 28:
                            meal_display = meal_display[:25] + '...'
                        draw.text((x_start + 10, y_pos), meal_display, 
                                 fill=self.config.text_color, font=self.font_tiny)
                        y_pos += 30
                        
                        # Calories and protein on same line
                        nutrition_text = f"{meal_info['calories']:.0f} cal | {meal_info['protein']:.0f}g protein"
                        draw.text((x_start + 10, y_pos), nutrition_text, 
                                 fill=self.config.success_color, font=self.font_tiny)
                        y_pos += 45
                        
                        break
            
            # Daily totals section with background
            totals = day_data['totals']
            totals_y = self.config.height - 250
            
            # Totals background box
            draw.rectangle([x_start - 10, totals_y, x_start + day_column_width - 50, totals_y + 150], 
                          fill=(30, 40, 50), outline=self.config.accent_color, width=2)
            
            # Daily totals header
            draw.text((x_start + 20, totals_y + 10), "DAILY TOTALS", 
                     fill=self.config.accent_color, font=self.font_small)
            
            # Calories
            draw.text((x_start + 20, totals_y + 45), f"{totals['calories']:.0f} calories", 
                     fill=self.config.text_color, font=self.font_medium)
            
            # Macros
            macro_text = f"P: {totals['protein']:.0f}g | C: {totals['carbs']:.0f}g | F: {totals['fat']:.0f}g"
            draw.text((x_start + 20, totals_y + 90), macro_text, 
                     fill=self.config.text_color, font=self.font_tiny)
            
            # Accuracy indicator
            cal_diff = abs(totals['calories'] - params.calories)
            accuracy = max(0, 100 - (cal_diff / params.calories * 100))
            accuracy_color = self.config.success_color if accuracy >= 95 else self.config.highlight_color
            accuracy_text = f"Accuracy: {accuracy:.0f}%"
            draw.text((x_start + 20, totals_y + 120), accuracy_text, 
                     fill=accuracy_color, font=self.font_tiny)
        
        # Week summary at bottom
        week_totals = {'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0}
        num_days = len(days_data)
        for day_data in days_data.values():
            for key in week_totals:
                week_totals[key] += day_data['totals'][key]
        
        # Average box
        avg_box_y = self.config.height - 70
        draw.rectangle([self.config.width//4, avg_box_y - 5, 3*self.config.width//4, avg_box_y + 35], 
                      fill=self.config.secondary_color)
        
        avg_text = f"Average: {week_totals['calories']/num_days:.0f} cal | {week_totals['protein']/num_days:.0f}g protein | {week_totals['carbs']/num_days:.0f}g carbs | {week_totals['fat']/num_days:.0f}g fat"
        self.center_text(draw, avg_text, avg_box_y + 5, self.font_small)
        
        return img
    
    def create_day_detail_slide(self, day_num: int, day_name: str, day_data: Dict) -> Image.Image:
        """Create enhanced detailed view of a single day"""
        img, draw = self.create_base_slide()
        
        # Header with gradient background
        header_gradient = [(13, 19, 23), (26, 38, 46)]
        for i in range(120):
            alpha = i / 120
            r = int(header_gradient[0][0] * (1 - alpha) + header_gradient[1][0] * alpha)
            g = int(header_gradient[0][1] * (1 - alpha) + header_gradient[1][1] * alpha)
            b = int(header_gradient[0][2] * (1 - alpha) + header_gradient[1][2] * alpha)
            draw.line([(0, i), (self.config.width, i)], fill=(r, g, b))
        
        # Day title
        self.center_text(draw, f"DAY {day_num} - {day_name.upper()}", 
                        40, self.font_body)
        
        # Day totals summary with visual bars
        totals = day_data['totals']
        summary = f"{totals['calories']:.0f} calories | Protein: {totals['protein']:.0f}g | Carbs: {totals['carbs']:.0f}g | Fat: {totals['fat']:.0f}g"
        self.center_text(draw, summary, 100, self.font_small)
        
        # Meals with enhanced layout
        y_start = 180
        meal_spacing = 140
        
        meal_order = ['breakfast', 'lunch', 'dinner', 'snack']
        sorted_meals = []
        
        for meal_type in meal_order:
            for meal_name, meal_data in day_data['meals'].items():
                if meal_type in meal_name.lower():
                    sorted_meals.append((meal_name, meal_data))
        
        for i, (meal_name, meal) in enumerate(sorted_meals):
            y_pos = y_start + i * meal_spacing
            
            # Meal card background
            draw.rectangle([60, y_pos - 10, self.config.width - 60, y_pos + 110],
                          fill=(25, 35, 45), outline=(40, 55, 70), width=2)
            
            # Meal type label with colored accent
            meal_label = meal_name.replace('_', ' ').title()
            accent_colors = {
                'breakfast': self.config.success_color,
                'lunch': self.config.accent_color,
                'dinner': self.config.highlight_color,
                'snack': self.config.secondary_color
            }
            
            meal_type = meal_name.split('_')[0] if '_' in meal_name else 'snack'
            accent_color = accent_colors.get(meal_type, self.config.accent_color)
            
            # Colored accent bar
            draw.rectangle([60, y_pos - 10, 70, y_pos + 110], fill=accent_color)
            
            draw.text((90, y_pos), meal_label.upper(), 
                     fill=accent_color, font=self.font_small)
            
            # Meal name
            draw.text((90, y_pos + 35), meal['name'], 
                     fill=self.config.text_color, font=self.font_medium)
            
            # Nutrition info with visual elements
            macro_y = y_pos + 75
            
            # Calorie badge
            cal_box_x = self.config.width - 250
            draw.rectangle([cal_box_x, y_pos + 10, cal_box_x + 150, y_pos + 60],
                          fill=accent_color, outline=None)
            draw.text((cal_box_x + 75, y_pos + 25), f"{meal['calories']:.0f}", 
                     fill=self.config.text_color, font=self.font_body, anchor="mm")
            draw.text((cal_box_x + 75, y_pos + 48), "calories", 
                     fill=self.config.text_color, font=self.font_tiny, anchor="mm")
            
            # Macro bars
            macros = [
                ('P', meal['protein'], self.config.success_color),
                ('C', meal['carbs'], self.config.highlight_color),
                ('F', meal['fat'], self.config.secondary_color)
            ]
            
            macro_x = 90
            for macro_label, value, color in macros:
                # Draw mini bar
                bar_width = min(100, value * 2)  # Scale for visual
                draw.rectangle([macro_x, macro_y, macro_x + bar_width, macro_y + 20],
                              fill=color, outline=None)
                draw.text((macro_x + 5, macro_y + 2), f"{macro_label}: {value:.0f}g", 
                         fill=self.config.text_color, font=self.font_tiny)
                macro_x += 120
            
            # Prep time if available
            if 'prep_time' in meal:
                draw.text((self.config.width - 350, macro_y), f"⏱ {meal['prep_time']} min prep", 
                         fill=(150, 150, 150), font=self.font_tiny)
        
        return img
    
    def create_shopping_list_slide(self, shopping_list: Dict[str, Dict[str, str]]) -> Image.Image:
        """Create enhanced shopping list with better organization"""
        img, draw = self.create_base_slide()
        
        # Title with shopping cart icon
        self.center_text(draw, "🛒 2-WEEK SHOPPING LIST", self.config.height // 10, self.font_title)
        
        # Organize categories in a more visual grid
        categories = list(shopping_list.keys())
        num_cols = 3
        num_rows = (len(categories) + num_cols - 1) // num_cols
        
        col_width = (self.config.width - 200) // num_cols
        row_height = (self.config.height - 300) // num_rows
        
        y_start = 180
        
        for i, category in enumerate(categories):
            col = i % num_cols
            row = i // num_cols
            
            x = 100 + col * col_width
            y = y_start + row * row_height
            
            # Category box
            box_colors = [
                self.config.accent_color,
                self.config.secondary_color,
                self.config.highlight_color
            ]
            box_color = box_colors[i % len(box_colors)]
            
            draw.rectangle([x, y, x + col_width - 40, y + 40], fill=box_color)
            
            # Category header
            draw.text((x + 20, y + 8), category.upper(), 
                     fill=self.config.text_color, font=self.font_small)
            
            # Items with checkboxes
            y_offset = y + 50
            items = shopping_list[category]
            max_items = 6  # Limit items shown
            
            for j, (item, amount) in enumerate(list(items.items())[:max_items]):
                # Checkbox
                draw.rectangle([x + 10, y_offset + 3, x + 22, y_offset + 15], 
                              outline=(150, 150, 150), width=2)
                
                # Item text
                item_text = f"{item}: {amount}"
                if len(item_text) > 25:
                    item_text = item_text[:22] + "..."
                    
                draw.text((x + 30, y_offset), item_text, 
                         fill=self.config.text_color, font=self.font_tiny)
                y_offset += 25
                
            if len(items) > max_items:
                draw.text((x + 30, y_offset), f"...+{len(items) - max_items} more", 
                         fill=(150, 150, 150), font=self.font_tiny)
        
        # Estimated cost section
        cost_box_y = self.config.height - 120
        draw.rectangle([self.config.width//4, cost_box_y, 3*self.config.width//4, cost_box_y + 60],
                      fill=(40, 50, 60), outline=self.config.accent_color, width=2)
        
        cost_text = "💰 Estimated cost: $150-180"
        self.center_text(draw, cost_text, cost_box_y + 15, self.font_body)
        tip_text = "Tip: Buy proteins in bulk and freeze portions"
        self.center_text(draw, tip_text, cost_box_y + 40, self.font_tiny, color=(150, 150, 150))
        
        return img
    
    def create_nutrition_summary_slide(self, week1_data: Dict, week2_data: Dict, params: MealPlanParameters) -> Image.Image:
        """Create enhanced nutrition summary with better visuals"""
        fig = plt.figure(figsize=(19.2, 10.8), facecolor='#0D1317')
        
        # Title with better styling
        fig.text(0.5, 0.95, 'NUTRITION ANALYSIS REPORT', fontsize=48, color='white', 
                ha='center', va='top', weight='bold')
        
        # Subtitle
        fig.text(0.5, 0.91, f'{params.diet_type.title()} Diet | {params.calories} Calories | {params.macro_goal.title()}',
                fontsize=20, color='#888888', ha='center', va='top')
        
        # Create subplots with better spacing
        gs = GridSpec(2, 3, figure=fig, hspace=0.35, wspace=0.35,
                     left=0.08, right=0.92, top=0.83, bottom=0.08)
        
        # 1. Daily Calorie Trend with target zone
        ax1 = fig.add_subplot(gs[0, :2])
        self._create_enhanced_calorie_trend(ax1, week1_data, week2_data, params.calories)
        
        # 2. Macro Distribution with targets
        ax2 = fig.add_subplot(gs[0, 2])
        self._create_enhanced_macro_pie(ax2, week1_data, week2_data, params)
        
        # 3. Protein Trend with recommendations
        ax3 = fig.add_subplot(gs[1, 0])
        self._create_enhanced_protein_trend(ax3, week1_data, week2_data, params)
        
        # 4. Meal Variety Score
        ax4 = fig.add_subplot(gs[1, 1])
        self._create_variety_score(ax4, week1_data, week2_data)
        
        # 5. Key Performance Indicators
        ax5 = fig.add_subplot(gs[1, 2])
        self._create_kpi_dashboard(ax5, week1_data, week2_data, params)
        
        plt.tight_layout()
        fig.canvas.draw()
        img = Image.frombytes('RGB', fig.canvas.get_width_height(), 
                             fig.canvas.tostring_rgb())
        plt.close()
        
        return img
    
    def _create_enhanced_calorie_trend(self, ax, week1_data, week2_data, target_calories):
        """Create enhanced 14-day calorie trend with target zone"""
        daily_calories = []
        
        for week_data in [week1_data, week2_data]:
            for day_name in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                if day_name in week_data:
                    daily_calories.append(week_data[day_name]['totals']['calories'])
        
        days = list(range(1, len(daily_calories) + 1))
        
        # Target zone (±5%)
        upper_bound = target_calories * 1.05
        lower_bound = target_calories * 0.95
        ax.fill_between(days, lower_bound, upper_bound, color='#0D7377', alpha=0.2, label='Target Zone')
        
        # Actual calories
        ax.plot(days, daily_calories, color='#FF6B35', linewidth=3, marker='o', 
                markersize=8, label='Actual', zorder=5)
        
        # Target line
        ax.axhline(y=target_calories, color='#0D7377', linestyle='--', linewidth=2, label='Target')
        
        # Styling
        ax.set_xlabel('Day', fontsize=14, color='white')
        ax.set_ylabel('Calories', fontsize=14, color='white')
        ax.set_title('Daily Calorie Intake vs Target', fontsize=18, color='white', pad=15)
        ax.legend(fontsize=12, loc='upper right')
        
        ax.set_facecolor('#1A1A1A')
        ax.grid(True, alpha=0.2)
        ax.tick_params(colors='white')
        
        for spine in ax.spines.values():
            spine.set_edgecolor('white')
            spine.set_alpha(0.3)
    
    def _create_enhanced_macro_pie(self, ax, week1_data, week2_data, params):
        """Create enhanced macro distribution pie chart with targets"""
        # Calculate average macros
        total_protein = total_carbs = total_fat = 0
        days = 0
        
        for week_data in [week1_data, week2_data]:
            for day_data in week_data.values():
                total_protein += day_data['totals']['protein']
                total_carbs += day_data['totals']['carbs']
                total_fat += day_data['totals']['fat']
                days += 1
        
        avg_protein = total_protein / days
        avg_carbs = total_carbs / days
        avg_fat = total_fat / days
        
        # Calculate percentages
        total_cal = (avg_protein * 4) + (avg_carbs * 4) + (avg_fat * 9)
        sizes = [
            (avg_protein * 4) / total_cal * 100,
            (avg_carbs * 4) / total_cal * 100,
            (avg_fat * 9) / total_cal * 100
        ]
        
        colors = ['#27AE60', '#FF6B35', '#F39C12']
        labels = [f'Protein\n{sizes[0]:.0f}%\n({avg_protein:.0f}g)', 
                  f'Carbs\n{sizes[1]:.0f}%\n({avg_carbs:.0f}g)', 
                  f'Fat\n{sizes[2]:.0f}%\n({avg_fat:.0f}g)']
        
        # Create donut chart
        wedges, texts = ax.pie(sizes, labels=labels, colors=colors, startangle=90,
                               textprops={'fontsize': 11, 'color': 'white'})
        
        # Create center circle for donut effect
        centre_circle = plt.Circle((0, 0), 0.70, fc='#1A1A1A')
        ax.add_artist(centre_circle)
        
        # Add center text
        ax.text(0, 0, 'MACROS', fontsize=16, color='white', ha='center', va='center', weight='bold')
        
        ax.set_title('Macro Distribution', fontsize=18, color='white', pad=15)
        ax.axis('equal')
    
    def _create_enhanced_protein_trend(self, ax, week1_data, week2_data, params):
        """Create enhanced protein intake trend with recommendations"""
        daily_protein = []
        
        for week_data in [week1_data, week2_data]:
            for day_name in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                if day_name in week_data:
                    daily_protein.append(week_data[day_name]['totals']['protein'])
        
        days = list(range(1, len(daily_protein) + 1))
        avg_protein = sum(daily_protein) / len(daily_protein)
        
        # Minimum recommended (0.8g per kg bodyweight, assuming 70kg)
        min_recommended = 56
        
        # Plot bars with color coding
        colors = ['#27AE60' if p >= min_recommended else '#E74C3C' for p in daily_protein]
        bars = ax.bar(days, daily_protein, color=colors, alpha=0.8)
        
        # Average and minimum lines
        ax.axhline(y=avg_protein, color='white', linestyle='--', linewidth=1, label=f'Avg: {avg_protein:.0f}g')
        ax.axhline(y=min_recommended, color='#E74C3C', linestyle='--', linewidth=1, label=f'Min: {min_recommended}g')
        
        ax.set_xlabel('Day', fontsize=14, color='white')
        ax.set_ylabel('Protein (g)', fontsize=14, color='white')
        ax.set_title('Daily Protein Intake', fontsize=18, color='white', pad=15)
        ax.legend(fontsize=10)
        
        ax.set_facecolor('#1A1A1A')
        ax.grid(True, axis='y', alpha=0.2)
        ax.tick_params(colors='white')
        
        for spine in ax.spines.values():
            spine.set_edgecolor('white')
            spine.set_alpha(0.3)
    
    def _create_variety_score(self, ax, week1_data, week2_data):
        """Create meal variety visualization"""
        ax.set_facecolor('#1A1A1A')
        ax.axis('off')
        
        # Count unique meals and cuisines
        unique_meals = set()
        cuisines = set()
        meal_types = {'breakfast': set(), 'lunch': set(), 'dinner': set(), 'snack': set()}
        
        for week in [week1_data, week2_data]:
            for day in week.values():
                for meal_name, meal in day['meals'].items():
                    unique_meals.add(meal['name'])
                    if 'cuisine' in meal:
                        cuisines.add(meal['cuisine'])
                    
                    # Categorize by meal type
                    for mtype in meal_types:
                        if mtype in meal_name.lower():
                            meal_types[mtype].add(meal['name'])
                            break
        
        # Calculate variety score
        total_meals = sum(len(day['meals']) for week in [week1_data, week2_data] for day in week.values())
        variety_score = (len(unique_meals) / total_meals) * 10 if total_meals > 0 else 0
        
        # Display metrics
        ax.text(0.5, 0.9, 'VARIETY METRICS', fontsize=18, color='white',
                ha='center', va='top', weight='bold')
        
        # Variety score gauge
        score_y = 0.65
        ax.text(0.5, score_y, f'Variety Score: {variety_score:.1f}/10',
                fontsize=24, color='#27AE60' if variety_score >= 7 else '#F39C12',
                ha='center', va='center', weight='bold')
        
        # Stats
        stats_y = 0.4
        stats = [
            f"Unique Recipes: {len(unique_meals)}",
            f"Cuisine Types: {len(cuisines)}",
            f"Breakfast Options: {len(meal_types['breakfast'])}",
            f"Lunch Options: {len(meal_types['lunch'])}",
            f"Dinner Options: {len(meal_types['dinner'])}"
        ]
        
        for i, stat in enumerate(stats):
            ax.text(0.5, stats_y - i*0.08, stat, fontsize=12, color='white',
                    ha='center', va='center')
    
    def _create_kpi_dashboard(self, ax, week1_data, week2_data, params):
        """Create key performance indicators dashboard"""
        ax.set_facecolor('#1A1A1A')
        ax.axis('off')
        
        ax.text(0.5, 0.9, 'KEY METRICS', fontsize=18, color='white',
                ha='center', va='top', weight='bold')
        
        # Calculate KPIs
        total_days = sum(len(week.keys()) for week in [week1_data, week2_data])
        
        # Calorie accuracy
        calorie_diffs = []
        for week in [week1_data, week2_data]:
            for day in week.values():
                diff = abs(day['totals']['calories'] - params.calories)
                calorie_diffs.append(diff)
        
        avg_cal_diff = sum(calorie_diffs) / len(calorie_diffs) if calorie_diffs else 0
        cal_accuracy = max(0, 100 - (avg_cal_diff / params.calories * 100))
        
        # Days within target
        days_on_target = sum(1 for diff in calorie_diffs if diff <= 50)
        
        # Average prep time
        total_prep = 0
        meal_count = 0
        for week in [week1_data, week2_data]:
            for day in week.values():
                for meal in day['meals'].values():
                    if 'prep_time' in meal:
                        total_prep += meal['prep_time']
                        meal_count += 1
        
        avg_prep = total_prep / meal_count if meal_count > 0 else 0
        
        # Display KPIs
        kpis = [
            ("Overall Accuracy", f"{cal_accuracy:.0f}%", 
             '#27AE60' if cal_accuracy >= 95 else '#F39C12'),
            ("Days on Target", f"{days_on_target}/{total_days}",
             '#27AE60' if days_on_target >= total_days * 0.8 else '#F39C12'),
            ("Avg Daily Error", f"{avg_cal_diff:.0f} cal",
             '#27AE60' if avg_cal_diff <= 50 else '#F39C12'),
            ("Avg Prep Time", f"{avg_prep:.0f} min",
             '#0D7377')
        ]
        
        y_pos = 0.65
        for label, value, color in kpis:
            ax.text(0.2, y_pos, label, fontsize=12, color='#888888', ha='left')
            ax.text(0.8, y_pos, value, fontsize=14, color=color, ha='right', weight='bold')
            y_pos -= 0.15
    
    def _add_decorative_corners(self, draw):
        """Add decorative corner elements"""
        corner_size = 50
        corner_width = 3
        
        # Top-left
        draw.line([(0, corner_size), (0, 0), (corner_size, 0)], 
                  fill=self.config.accent_color, width=corner_width)
        
        # Top-right
        draw.line([(self.config.width - corner_size, 0), (self.config.width, 0), 
                   (self.config.width, corner_size)], 
                  fill=self.config.accent_color, width=corner_width)
        
        # Bottom-left
        draw.line([(0, self.config.height - corner_size), (0, self.config.height), 
                   (corner_size, self.config.height)], 
                  fill=self.config.accent_color, width=corner_width)
        
        # Bottom-right
        draw.line([(self.config.width - corner_size, self.config.height), 
                   (self.config.width, self.config.height), 
                   (self.config.width, self.config.height - corner_size)], 
                  fill=self.config.accent_color, width=corner_width)

class VideoCreator:
    """Creates videos from slides with tracking for YouTube timestamps"""
    
    def __init__(self, config: VideoConfig):
        self.config = config
        self.slide_generator = SlideGenerator(config)
        self.optimizer = MealPlanOptimizer()
        self.timestamps = []  # Track timestamps for YouTube
        self.current_time = 0  # Track current video time
    
    def _add_timestamp(self, description: str):
        """Add a timestamp entry"""
        minutes = int(self.current_time // 60)
        seconds = int(self.current_time % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        self.timestamps.append((timestamp, description))
    
    def create_longform_video(self, params: MealPlanParameters, output_path: str):
        """Create full longform video with complete week overviews"""
        slides = []
        self.timestamps = []
        self.current_time = 0
        
        # Generate 2-week meal plan
        print("Generating 2-week meal plan...")
        preferences = params.to_optimizer_preferences()
        
        # Initialize meal history
        meal_history = {}
        
        # Generate Week 1
        week1 = self.optimizer.generate_week_plan_enhanced(preferences, 1, meal_history)
        
        # Generate Week 2
        week2 = self.optimizer.generate_week_plan_enhanced(preferences, 2, meal_history)
        
        # Generate shopping list
        meal_plan = {
            'preferences': preferences,
            'week1': week1,
            'week2': week2
        }
        shopping_list = self.optimizer.generate_shopping_list(meal_plan)
        
        # Create slides with timestamps
        # 1. Title (5 sec)
        self._add_timestamp("Introduction")
        slides.append((self.slide_generator.create_title_slide(params), 5))
        self.current_time += 5
        
        # 2. Week 1 Full Overview (12 sec)
        self._add_timestamp("Week 1 Complete Overview")
        slides.append((self.slide_generator.create_full_week_overview_slide(1, week1, params), 12))
        self.current_time += 12
        
        # 3. Week 1 Split Views
        # Week 1: Monday-Thursday (10 sec)
        self._add_timestamp("Week 1: Monday-Thursday")
        week1_part1 = {k: v for k, v in week1.items() if k in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']}
        slides.append((self.slide_generator.create_week_overview_slide(1, week1_part1, "MON-THU", params), 10))
        self.current_time += 10
        
        # Week 1: Friday-Sunday (8 sec)
        self._add_timestamp("Week 1: Friday-Sunday")
        week1_part2 = {k: v for k, v in week1.items() if k in ['Friday', 'Saturday', 'Sunday']}
        slides.append((self.slide_generator.create_week_overview_slide(1, week1_part2, "FRI-SUN", params), 8))
        self.current_time += 8
        
        # 4. Week 1 Daily Details (7 days x 6 sec = 42 sec)
        day_counter = 0
        for day_name in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            if day_name in week1:
                day_counter += 1
                self._add_timestamp(f"Week 1 - {day_name}")
                slides.append((self.slide_generator.create_day_detail_slide(
                    day_counter, day_name, week1[day_name]
                ), 6))
                self.current_time += 6
        
        # 5. Week 2 Full Overview (12 sec)
        self._add_timestamp("Week 2 Complete Overview")
        slides.append((self.slide_generator.create_full_week_overview_slide(2, week2, params), 12))
        self.current_time += 12
        
        # 6. Week 2 Split Views
        # Week 2: Monday-Thursday (10 sec)
        self._add_timestamp("Week 2: Monday-Thursday")
        week2_part1 = {k: v for k, v in week2.items() if k in ['Monday', 'Tuesday', 'Wednesday', 'Thursday']}
        slides.append((self.slide_generator.create_week_overview_slide(2, week2_part1, "MON-THU", params), 10))
        self.current_time += 10
        
        # Week 2: Friday-Sunday (8 sec)
        self._add_timestamp("Week 2: Friday-Sunday")
        week2_part2 = {k: v for k, v in week2.items() if k in ['Friday', 'Saturday', 'Sunday']}
        slides.append((self.slide_generator.create_week_overview_slide(2, week2_part2, "FRI-SUN", params), 8))
        self.current_time += 8
        
        # 7. Week 2 Daily Details (7 days x 6 sec = 42 sec)
        for day_name in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
            if day_name in week2:
                day_counter += 1
                self._add_timestamp(f"Week 2 - {day_name}")
                slides.append((self.slide_generator.create_day_detail_slide(
                    day_counter, day_name, week2[day_name]
                ), 6))
                self.current_time += 6
        
        # 8. Shopping List (10 sec)
        self._add_timestamp("Shopping List")
        slides.append((self.slide_generator.create_shopping_list_slide(shopping_list), 10))
        self.current_time += 10
        
        # 9. Nutrition Summary (10 sec)
        self._add_timestamp("Nutrition Analysis")
        slides.append((self.slide_generator.create_nutrition_summary_slide(week1, week2, params), 10))
        self.current_time += 10
        
        # Create video
        self._create_video_from_slides(slides, output_path, params.get_filename_base())
        
        # Save meal plan data and YouTube metadata
        self._save_meal_plan_data(params, week1, week2, shopping_list, output_path)
        self._save_youtube_metadata(params, output_path)
    
    def create_shorts_video(self, params: MealPlanParameters, output_path: str):
        """Create YouTube Shorts with hooks"""
        slides = []
        
        # Quick generation for shorts
        preferences = params.to_optimizer_preferences()
        meal_history = {}
        week1 = self.optimizer.generate_week_plan_enhanced(preferences, 1, meal_history)
        
        # Calculate interesting stats from week 1
        total_protein = sum(day['totals']['protein'] for day in week1.values()) / 7
        total_calories = sum(day['totals']['calories'] for day in week1.values()) / 7
        
        # Find highest protein meal
        highest_protein_meal = None
        highest_protein = 0
        for day_data in week1.values():
            for meal_name, meal in day_data['meals'].items():
                if meal['protein'] > highest_protein:
                    highest_protein = meal['protein']
                    highest_protein_meal = meal
        
        # Type 1: High Performance Hook
        if params.macro_goal in ["high protein", "balanced"]:
            # Hook slide (3 sec)
            hook_slide = self._create_shorts_hook_slide(
                f"WANT {total_protein:.0f}g PROTEIN",
                "EVERY SINGLE DAY?",
                "HERE'S HOW →"
            )
            slides.append((hook_slide, 3))
            
            # Show top 3 protein meals (15 sec)
            protein_meals = []
            for day_data in week1.values():
                for meal in day_data['meals'].values():
                    protein_meals.append(meal)
            protein_meals.sort(key=lambda x: x['protein'], reverse=True)
            
            for i, meal in enumerate(protein_meals[:3]):
                meal_slide = self._create_shorts_meal_slide(meal, i+1)
                slides.append((meal_slide, 5))
            
            # Result slide (7 sec)
            result_slide = self._create_shorts_result_slide(
                f"AVG: {total_protein:.0f}g PROTEIN DAILY",
                f"FROM {params.calories} CALORIES",
                "GET FULL PLAN - LINK IN BIO"
            )
            slides.append((result_slide, 7))
            
        # Type 2: Weight Loss Hook
        elif params.calories <= 1800:
            # Hook slide (3 sec)
            hook_slide = self._create_shorts_hook_slide(
                "LOSING WEIGHT?",
                f"EAT {params.calories} CALORIES",
                "& NEVER GO HUNGRY →"
            )
            slides.append((hook_slide, 3))
            
            # Show satisfying meals (15 sec)
            day_num = 0
            for day_name, day_data in list(week1.items())[:3]:
                day_num += 1
                day_slide = self._create_shorts_day_slide(day_num, day_data)
                slides.append((day_slide, 5))
            
            # Result slide (7 sec)
            result_slide = self._create_shorts_result_slide(
                "14 DAYS PLANNED",
                "SHOPPING LIST READY",
                "START TODAY - LINK IN BIO"
            )
            slides.append((result_slide, 7))
            
        # Type 3: Keto/Special Diet Hook
        else:
            # Hook slide (3 sec)
            diet_name = params.diet_type.upper()
            hook_slide = self._create_shorts_hook_slide(
                f"{diet_name} DIET?",
                "MEAL PLANNING SUCKS?",
                "FIXED IT FOR YOU →"
            )
            slides.append((hook_slide, 3))
            
            # Show variety of meals (15 sec)
            meal_samples = []
            for day_data in week1.values():
                for meal in day_data['meals'].values():
                    meal_samples.append(meal)
                    if len(meal_samples) >= 3:
                        break
                if len(meal_samples) >= 3:
                    break
            
            for i, meal in enumerate(meal_samples[:3]):
                meal_slide = self._create_shorts_meal_slide(meal, i+1, show_macros=True)
                slides.append((meal_slide, 5))
            
            # Result slide (7 sec)
            result_slide = self._create_shorts_result_slide(
                "2 WEEKS DONE FOR YOU",
                "ZERO GUESSWORK",
                "DOWNLOAD NOW - LINK IN BIO"
            )
            slides.append((result_slide, 7))
        
        # Create video
        output_file = f"{params.get_filename_base()}_shorts.mp4"
        self._create_video_from_slides(slides, output_path, output_file, fps=30, is_shorts=True)
    
    def _create_shorts_hook_slide(self, line1: str, line2: str, line3: str) -> Image.Image:
        """Create hook slide for shorts with animation hints"""
        img, draw = self.slide_generator.create_base_slide()
        
        # Vertical format adjustments
        center_x = self.config.width // 2
        
        # Add visual elements
        # Top accent bar
        draw.rectangle([0, 0, self.config.width, 100], fill=self.config.accent_color)
        
        # Main text with different sizes for emphasis
        draw.text((center_x - 300, self.config.height // 3), line1,
                 fill=self.config.text_color, font=self.slide_generator.font_body)
        
        draw.text((center_x - 350, self.config.height // 2), line2,
                 fill=self.config.highlight_color, font=self.slide_generator.font_title)
        
        # Call to action with arrow
        draw.text((center_x - 200, 2 * self.config.height // 3), line3,
                 fill=self.config.success_color, font=self.slide_generator.font_body)
        
        # Add arrow pointing down
        arrow_x = center_x + 150
        arrow_y = 2 * self.config.height // 3 + 20
        draw.polygon([(arrow_x, arrow_y), (arrow_x - 20, arrow_y - 20), 
                     (arrow_x + 20, arrow_y - 20)], fill=self.config.success_color)
        
        return img
    
    def _create_shorts_meal_slide(self, meal: Dict, number: int, show_time: bool = False, 
                                 show_macros: bool = False) -> Image.Image:
        """Create meal showcase slide for shorts"""
        img, draw = self.slide_generator.create_base_slide()
        
        # Number badge in corner
        draw.ellipse([50, 50, 150, 150], fill=self.config.accent_color)
        draw.text((100, 100), f"#{number}", 
                 fill=self.config.text_color, font=self.slide_generator.font_title,
                 anchor="mm")
        
        # Meal name (larger)
        meal_name = meal['name']
        if len(meal_name) > 30:
            meal_name = meal_name[:27] + '...'
        self.slide_generator.center_text(draw, meal_name, 
                                        self.config.height // 3, 
                                        self.slide_generator.font_body)
        
        # Big calorie display
        stats_y = self.config.height // 2
        
        # Try to create a large font, fallback to available font
        try:
            large_font = ImageFont.truetype(self.slide_generator.font_path if hasattr(self.slide_generator, 'font_path') else 'arial.ttf', 120)
        except (IOError, OSError) as e:
            self.logger.warning(f"Failed to load large font: {str(e)}")
            large_font = self.slide_generator.font_title or ImageFont.load_default()
        
        self.slide_generator.center_text(draw, f"{meal['calories']:.0f}", 
                                        stats_y, 
                                        large_font)
        
        self.slide_generator.center_text(draw, "CALORIES", 
                                        stats_y + 100, 
                                        self.slide_generator.font_body)
        
        # Protein highlight
        protein_y = stats_y + 200
        draw.rectangle([self.config.width // 4, protein_y - 40, 
                       3 * self.config.width // 4, protein_y + 40],
                       fill=self.config.success_color)
        
        self.slide_generator.center_text(draw, f"{meal['protein']:.0f}g PROTEIN", 
                                        protein_y, 
                                        self.slide_generator.font_body)
        
        if show_macros:
            macro_y = protein_y + 100
            macro_text = f"C: {meal['carbs']:.0f}g | F: {meal['fat']:.0f}g"
            self.slide_generator.center_text(draw, macro_text, 
                                            macro_y, 
                                            self.slide_generator.font_small)
        
        if show_time and 'prep_time' in meal:
            self.slide_generator.center_text(draw, f"⏱ {meal['prep_time']} MIN", 
                                            self.config.height - 200, 
                                            self.slide_generator.font_body)
        
        return img
    
    def _create_shorts_day_slide(self, day_num: int, day_data: Dict) -> Image.Image:
        """Create day summary slide for shorts"""
        img, draw = self.slide_generator.create_base_slide()
        
        # Day header
        self.slide_generator.center_text(draw, f"DAY {day_num}", 
                                        self.config.height // 6, 
                                        self.slide_generator.font_title)
        
        # Meals list (compact)
        y_offset = self.config.height // 3
        for meal_name, meal in day_data['meals'].items():
            meal_type = meal_name.replace('_', ' ').title()
            
            # Meal type label
            draw.text((100, y_offset), meal_type.upper(), 
                     fill=self.config.accent_color, font=self.slide_generator.font_small)
            
            # Meal name (abbreviated)
            meal_display = meal['name'][:25] + '...' if len(meal['name']) > 25 else meal['name']
            draw.text((100, y_offset + 30), meal_display, 
                     fill=self.config.text_color, font=self.slide_generator.font_tiny)
            
            # Calories on right
            draw.text((self.config.width - 200, y_offset + 15), f"{meal['calories']:.0f} cal", 
                     fill=self.config.success_color, font=self.slide_generator.font_small)
            
            y_offset += 80
        
        # Total at bottom
        totals = day_data['totals']
        total_box_y = 2 * self.config.height // 3
        draw.rectangle([self.config.width // 4, total_box_y, 
                       3 * self.config.width // 4, total_box_y + 80],
                       fill=self.config.secondary_color)
        
        self.slide_generator.center_text(draw, f"TOTAL: {totals['calories']:.0f} CAL", 
                                        total_box_y + 40, 
                                        self.slide_generator.font_body)
        
        return img
    
    def _create_shorts_result_slide(self, line1: str, line2: str, cta: str) -> Image.Image:
        """Create result/CTA slide for shorts"""
        img, draw = self.slide_generator.create_base_slide()
        
        # Success checkmark
        check_y = self.config.height // 4
        draw.ellipse([self.config.width // 2 - 60, check_y - 60, 
                     self.config.width // 2 + 60, check_y + 60],
                    fill=self.config.success_color)
        
        # Try to create a large font for checkmark, fallback to available font
        try:
            check_font = ImageFont.truetype(self.slide_generator.font_path if hasattr(self.slide_generator, 'font_path') else 'arial.ttf', 80)
        except (IOError, OSError) as e:
            self.logger.warning(f"Failed to load check font: {str(e)}")
            check_font = self.slide_generator.font_title or ImageFont.load_default()
        
        self.slide_generator.center_text(draw, "✓", check_y, check_font)
        
        # Results text
        self.slide_generator.center_text(draw, line1, 
                                        self.config.height // 2 - 50, 
                                        self.slide_generator.font_body)
        
        self.slide_generator.center_text(draw, line2, 
                                        self.config.height // 2 + 50, 
                                        self.slide_generator.font_body)
        
        # CTA box with pulsing hint
        box_y = 3 * self.config.height // 4
        
        # Outer glow
        for i in range(3):
            alpha = 50 - i * 15
            glow_rect = [self.config.width//4 - i*5, box_y - 50 - i*5, 
                        3*self.config.width//4 + i*5, box_y + 50 + i*5]
            draw.rectangle(glow_rect, outline=self.config.accent_color, width=2)
        
        # Main CTA box
        draw.rectangle([self.config.width//4, box_y - 40, 
                       3*self.config.width//4, box_y + 40],
                      fill=self.config.accent_color)
        
        self.slide_generator.center_text(draw, cta, box_y, 
                                        self.slide_generator.font_body)
        
        # Add urgency text
        urgency_text = "⚡ LIMITED TIME FREE ACCESS ⚡"
        self.slide_generator.center_text(draw, urgency_text, 
                                        self.config.height - 100, 
                                        self.slide_generator.font_small,
                                        color=self.config.highlight_color)
        
        return img
    
    def _create_video_from_slides(self, slides: List[Tuple[Image.Image, int]], 
                                 output_path: str, filename: str, fps: int = 30,
                                 is_shorts: bool = False):
        """Convert slides to video file with smooth transitions"""
        if is_shorts:
            # Vertical format for shorts
            width, height = 1080, 1920
        else:
            width, height = self.config.width, self.config.height
        
        output_file = os.path.join(output_path, f"{filename}.mp4")
        
        # Create video writer with better codec
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
        
        # Add transition frames between slides
        for i, (slide_img, duration_seconds) in enumerate(slides):
            # Resize if needed for shorts
            if is_shorts:
                slide_img = slide_img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert PIL to OpenCV format
            frame = cv2.cvtColor(np.array(slide_img), cv2.COLOR_RGB2BGR)
            
            # Add fade in for first frame
            if i == 0:
                for alpha in range(0, 100, 5):
                    fade_frame = cv2.addWeighted(frame, alpha/100, 
                                               np.zeros_like(frame), 1-alpha/100, 0)
                    out.write(fade_frame)
            
            # Write frame for duration
            for _ in range(fps * duration_seconds):
                out.write(frame)
            
            # Add crossfade to next slide (except last)
            if i < len(slides) - 1:
                next_slide, _ = slides[i + 1]
                if is_shorts:
                    next_slide = next_slide.resize((width, height), Image.Resampling.LANCZOS)
                next_frame = cv2.cvtColor(np.array(next_slide), cv2.COLOR_RGB2BGR)
                
                # Crossfade over 0.5 seconds
                for j in range(fps // 2):
                    alpha = j / (fps // 2)
                    fade_frame = cv2.addWeighted(frame, 1-alpha, next_frame, alpha, 0)
                    out.write(fade_frame)
        
        # Add fade out for last frame
        for alpha in range(100, 0, -5):
            fade_frame = cv2.addWeighted(frame, alpha/100, 
                                       np.zeros_like(frame), 1-alpha/100, 0)
            out.write(fade_frame)
        
        out.release()
        cv2.destroyAllWindows()
        print(f"Video created: {output_file}")
    
    def _save_meal_plan_data(self, params: MealPlanParameters, week1: Dict, week2: Dict, 
                            shopping_list: Dict, output_path: str):
        """Save meal plan data for reference"""
        data = {
            'parameters': {
                'diet_type': params.diet_type,
                'calories': params.calories,
                'macro_goal': params.macro_goal,
                'meal_structure': params.meal_structure
            },
            'week1': week1,
            'week2': week2,
            'shopping_list': shopping_list,
            'generated': datetime.now().isoformat()
        }
        
        output_file = os.path.join(output_path, f"{params.get_filename_base()}_plan.json")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Meal plan data saved: {output_file}")
    
    def _save_youtube_metadata(self, params: MealPlanParameters, output_path: str):
        """Save YouTube metadata with timestamps"""
        # Create title
        title = f"{params.calories} Calorie {params.diet_type.title()} Meal Plan | 14 Days | {params.macro_goal.title()}"
        
        # Create description
        description = f"""Complete 14-day {params.diet_type} meal plan with {params.calories} calories per day!

✅ WHAT'S INCLUDED:
- 2 full weeks of meals planned
- {params.macro_goal.title()} macro distribution
- Complete shopping list
- Meal prep times included
- Daily nutrition breakdowns

📊 MEAL PLAN DETAILS:
- Diet Type: {params.diet_type.title()}
- Daily Calories: {params.calories}
- Macro Focus: {params.macro_goal.title()}
- Meal Schedule: {params.meal_structure}

⏱️ TIMESTAMPS:
{chr(10).join([f'{time} - {desc}' for time, desc in self.timestamps])}

🔗 RESOURCES:
- Download PDF: [Your Website]/meal-plans/{params.get_filename_base()}
- Nutrition Calculator: [Your Website]/calculator
- Join Community: [Your Website]/community

📱 FOLLOW FOR MORE:
- Instagram: @YourHandle
- TikTok: @YourHandle
- Website: YourWebsite.com

#MealPlanning #{params.diet_type}Diet #MealPrep #Nutrition #HealthyEating #{params.calories}Calories"""
        
        # Create tags
        tags = [
            "meal planning",
            "meal prep",
            f"{params.diet_type} diet",
            f"{params.diet_type} meal plan",
            f"{params.calories} calorie diet",
            f"{params.calories} calorie meal plan",
            "nutrition",
            "healthy eating",
            "weight loss" if params.calories <= 1800 else "muscle building",
            "diet plan",
            "weekly meal prep",
            "healthy recipes",
            params.macro_goal,
            "meal plan with grocery list"
        ]
        
        # Create metadata object
        metadata = YouTubeMetadata(
            title=title,
            description=description,
            tags=tags,
            timestamps=self.timestamps
        )
        
        # Save to file
        output_file = os.path.join(output_path, f"{params.get_filename_base()}_youtube.txt")
        with open(output_file, 'w') as f:
            f.write(metadata.to_string())
        
        print(f"YouTube metadata saved: {output_file}")

class CibozerVideoGenerator:
    """Main class for generating Cibozer videos"""
    
    def __init__(self):
        self.config = VideoConfig()
        self.video_creator = VideoCreator(self.config)
        self.optimizer = MealPlanOptimizer()
        
        self.diet_types = ["omnivore", "vegetarian", "vegan", "pescatarian", 
                          "keto", "low-carb", "paleo", "gluten-free"]
        self.calorie_targets = [1200, 1500, 1800, 2000, 2500, 3000, 3500]
        self.macro_goals = ["high protein", "balanced", "high carb", 
                           "keto ratios", "mediterranean", "low fat"]
        self.meal_structures = ["3 meals", "3+2", "5 small", "2 meals", "OMAD"]
    
    def generate_video(self, diet_type: str, calories: int, 
                      macro_goal: str, meal_structure: str,
                      output_path: str = "./output"):
        """Generate both longform and shorts videos with input validation"""
        
        # Validate output path
        if not isinstance(output_path, str):
            raise ValueError(f"Output path must be a string, got: {type(output_path)}")
        
        # Validate output path is writable
        try:
            os.makedirs(output_path, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise ValueError(f"Cannot create output directory '{output_path}': {e}")
        
        # Create and validate parameters (validation happens in __post_init__)
        try:
            params = MealPlanParameters(
                calories=calories,
                diet_type=diet_type,
                macro_goal=macro_goal,
                meal_structure=meal_structure
            )
        except ValueError as e:
            print(f"[ERROR] Invalid parameters: {e}")
            print("\nValid options:")
            print(f"  Diet types: {', '.join(self.diet_types)}")
            print(f"  Calorie range: 800-5000 (recommended: 1200-3500)")
            print(f"  Macro goals: {', '.join(self.macro_goals)}")
            print(f"  Meal structures: {', '.join(self.meal_structures)}")
            raise
        
        # Generate videos
        print(f"\nGenerating videos for: {params.get_filename_base()}")
        print("This will create meal planning videos with full week overviews...")
        
        self.video_creator.create_longform_video(params, output_path)
        self.video_creator.create_shorts_video(params, output_path)
        
        # Generate metadata
        self._generate_metadata(params, output_path)
    
    def _generate_metadata(self, params: MealPlanParameters, output_path: str):
        """Generate metadata files for the video"""
        
        # Video titles
        title_longform = f"{params.calories} Calorie {params.diet_type.title()} Meal Plan | 14 Days | {params.macro_goal.title()}"
        title_shorts = f"{params.diet_type.title()} Diet - {params.calories} Cal/Day #mealprep #shorts"
        
        # Save metadata
        metadata = {
            "longform": {
                "title": title_longform,
                "filename": f"{params.get_filename_base()}.mp4"
            },
            "shorts": {
                "title": title_shorts,
                "filename": f"{params.get_filename_base()}_shorts.mp4"
            },
            "parameters": {
                "calories": params.calories,
                "diet_type": params.diet_type,
                "macro_goal": params.macro_goal,
                "meal_structure": params.meal_structure
            },
            "generated": datetime.now().isoformat()
        }
        
        metadata_file = os.path.join(output_path, f"{params.get_filename_base()}_metadata.json")
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Metadata saved: {metadata_file}")

def main():
    """Main function to generate videos"""
    generator = CibozerVideoGenerator()
    
    # Example: Generate single video
    generator.generate_video(
        diet_type="vegan",
        calories=2000,
        macro_goal="high protein", 
        meal_structure="3+2",
        output_path="./cibozer_output"
    )

if __name__ == "__main__":
    main()