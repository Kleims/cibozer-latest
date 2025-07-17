# video_generator.py - Updated to support both legacy and Cibozer formats

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle
import cv2
from typing import Dict, List, Tuple
import json
import nutrition_data as nd
from cibozer import CibozerVideoGenerator, MealPlanParameters

class VideoGenerator:
    """Legacy video generator with Cibozer integration option"""
    
    def __init__(self, meal_plan_data: Dict):
        self.plan = meal_plan_data
        self.preferences = meal_plan_data['preferences']
        self.diet_profiles = nd.DIET_PROFILES
        self.meal_patterns = nd.MEAL_PATTERNS
        
        # Enhanced color scheme - softer, more elegant
        self.colors = {
            'background': '#FAFAFA',    # Soft white
            'text': '#1A1A1A',          # Soft black
            'primary': '#2C3E50',       # Sophisticated blue-gray
            'secondary': '#7F8C8D',     # Muted gray
            'accent': '#E74C3C',        # Elegant red accent
            'light_gray': '#ECF0F1',    # Very light gray
            'success': '#27AE60',       # Emerald green
            'warning': '#F39C12',       # Amber
            'error': '#E74C3C',         # Red
            'table_header': '#34495E',  # Dark blue-gray
            'table_row1': '#FFFFFF',    # White
            'table_row2': '#F8F9FA',    # Light gray alternate
        }
        
        # Video settings
        self.fps = 30
        self.width = 1920
        self.height = 1080
        self.dpi = 100
        
        # Frame durations
        self.title_duration = 4
        self.summary_duration = 6
        self.week_table_duration = 8
        self.day_detail_duration = 5
        self.report_duration = 7
        self.transition_frames = 15  # Number of frames for fade transition
        
        # Enhanced font settings
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
        plt.rcParams['axes.linewidth'] = 0
        plt.rcParams['xtick.major.width'] = 0
        plt.rcParams['ytick.major.width'] = 0
    
    def create_cibozer_version(self, output_path: str = "./cibozer_output"):
        """Create Cibozer-style video from legacy meal plan"""
        print("\n🔄 Converting to Cibozer format...")
        
        # Extract parameters from meal plan
        diet_map = {
            'standard': 'omnivore',
            'keto': 'keto',
            'vegan': 'vegan',
            'vegetarian': 'vegetarian',
            'paleo': 'paleo',
            'mediterranean': 'pescatarian',
            'carnivore': 'omnivore',
            'pescatarian': 'pescatarian'
        }
        
        pattern_map = {
            'standard': '3 meals',
            '16_8_if': '2 meals',
            '18_6_if': '2 meals',
            'omad': 'OMAD',
            'bodybuilding': '5 small',
            'athlete': '3+2'
        }
        
        # Determine macro goal from diet
        macro_map = {
            'keto': 'keto ratios',
            'paleo': 'high protein',
            'carnivore': 'high protein',
            'standard': 'balanced',
            'vegan': 'balanced',
            'vegetarian': 'balanced',
            'mediterranean': 'mediterranean',
            'pescatarian': 'mediterranean'
        }
        
        # Create Cibozer parameters
        params = MealPlanParameters(
            calories=self.preferences['calories'],
            diet_type=diet_map.get(self.preferences['diet'], 'omnivore'),
            macro_goal=macro_map.get(self.preferences['diet'], 'balanced'),
            meal_structure=pattern_map.get(self.preferences['pattern'], '3 meals')
        )
        
        # Initialize Cibozer generator
        cibozer = CibozerVideoGenerator()
        
        # Create output directory
        os.makedirs(output_path, exist_ok=True)
        
        # Generate Cibozer videos using the meal plan data
        print(f"Generating Cibozer videos for: {params.get_filename_base()}")
        cibozer.video_creator.create_longform_video(params, output_path)
        cibozer.video_creator.create_shorts_video(params, output_path)
        
        print(f"\n✅ Cibozer videos created in: {output_path}")
    
    # Keep all original methods for legacy support
    def create_transition(self, frame1_path: str, frame2_path: str) -> List[np.ndarray]:
        """Create smooth fade transition between two frames"""
        img1 = cv2.imread(frame1_path)
        img2 = cv2.imread(frame2_path)
        
        if img1 is None or img2 is None:
            return []
        
        transition_frames = []
        for i in range(self.transition_frames):
            # Use ease-in-out curve for smoother transition
            t = i / self.transition_frames
            # Smoothstep function
            t = t * t * (3.0 - 2.0 * t)
            
            blended = cv2.addWeighted(img1, 1-t, img2, t, 0)
            transition_frames.append(blended)
        
        return transition_frames
    
    def create_title_frame(self) -> plt.Figure:
        """Create elegant title frame"""
        fig, ax = plt.subplots(figsize=(self.width/self.dpi, self.height/self.dpi), 
                               facecolor=self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # Subtle background gradient effect using rectangles
        for i in range(10):
            alpha = 0.02 * (10 - i)
            rect = Rectangle((0, 0.4 + i*0.06), 1, 0.06, 
                           facecolor=self.colors['primary'], alpha=alpha)
            ax.add_patch(rect)
        
        # Main title
        diet_name = self.diet_profiles[self.preferences['diet']]['name']
        ax.text(0.5, 0.6, diet_name.upper(), 
                fontsize=72, color=self.colors['primary'],
                ha='center', va='center', weight='200',
                fontfamily='sans-serif')
        
        # Subtitle with elegant spacing
        ax.text(0.5, 0.48, "PERSONALIZED MEAL PLAN",
                fontsize=32, color=self.colors['secondary'],
                ha='center', va='center', weight='300')
        
        # Elegant divider
        ax.plot([0.3, 0.7], [0.4, 0.4], color=self.colors['accent'], 
                linewidth=2, alpha=0.8)
        
        # Duration
        ax.text(0.5, 0.3, "14-Day Optimized Journey",
                fontsize=24, color=self.colors['secondary'],
                ha='center', va='center', weight='300')
        
        plt.tight_layout(pad=0)
        return fig
    
    def create_summary_frame(self) -> plt.Figure:
        """Create plan summary frame with key parameters"""
        fig, ax = plt.subplots(figsize=(self.width/self.dpi, self.height/self.dpi),
                               facecolor=self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # Header
        ax.text(0.5, 0.92, "MEAL PLAN OVERVIEW",
                fontsize=48, color=self.colors['primary'],
                ha='center', va='top', weight='200')
        
        # Elegant underline
        ax.plot([0.25, 0.75], [0.87, 0.87], color=self.colors['accent'], 
                linewidth=2, alpha=0.8)
        
        # Get diet profile info
        diet_profile = self.diet_profiles[self.preferences['diet']]
        target_macros = diet_profile['macros']
        
        # Left column - Plan Details
        x_left = 0.15
        y_start = 0.75
        line_height = 0.06
        
        # Diet Type
        ax.text(x_left, y_start, "DIET TYPE", fontsize=14, 
                color=self.colors['secondary'], weight='600')
        ax.text(x_left, y_start - 0.025, diet_profile['name'], 
                fontsize=24, color=self.colors['primary'], weight='400')
        
        # Calorie Target
        y_start -= line_height * 1.5
        ax.text(x_left, y_start, "DAILY CALORIES", fontsize=14,
                color=self.colors['secondary'], weight='600')
        ax.text(x_left, y_start - 0.025, f"{self.preferences['calories']:,}", 
                fontsize=24, color=self.colors['primary'], weight='400')
        
        # Meal Pattern
        y_start -= line_height * 1.5
        pattern_name = self.meal_patterns[self.preferences['pattern']]['name']
        ax.text(x_left, y_start, "MEAL SCHEDULE", fontsize=14,
                color=self.colors['secondary'], weight='600')
        ax.text(x_left, y_start - 0.025, pattern_name, 
                fontsize=24, color=self.colors['primary'], weight='400')
        
        # Right column - Macro Targets
        x_right = 0.55
        y_start = 0.75
        
        ax.text(x_right, y_start, "MACRO TARGETS", fontsize=14,
                color=self.colors['secondary'], weight='600')
        
        # Macro breakdown
        macros = [
            ('Protein', target_macros['protein'], self.colors['success']),
            ('Fat', target_macros['fat'], self.colors['warning']),
            ('Carbs', target_macros['carbs'], self.colors['accent'])
        ]
        
        y_macro = y_start - 0.04
        for macro, value, color in macros:
            # Macro name and percentage
            ax.text(x_right, y_macro, f"{macro}:", fontsize=20,
                    color=self.colors['primary'], weight='400')
            ax.text(x_right + 0.15, y_macro, f"{value}%", fontsize=20,
                    color=color, weight='500')
            
            # Visual bar
            bar_width = 0.2 * (value / 100)
            rect = Rectangle((x_right + 0.22, y_macro - 0.005), bar_width, 0.015,
                           facecolor=color, alpha=0.3)
            ax.add_patch(rect)
            
            y_macro -= 0.05
        
        # Description
        ax.text(0.5, 0.25, diet_profile['description'],
                fontsize=18, color=self.colors['secondary'],
                ha='center', va='center', weight='300',
                wrap=True, style='italic')
        
        # Who it's for
        if self.preferences['diet'] == 'keto':
            target_audience = "Ideal for rapid weight loss and mental clarity"
        elif self.preferences['diet'] == 'vegan':
            target_audience = "Perfect for plant-based lifestyle and environmental consciousness"
        elif self.preferences['diet'] == 'high_protein':
            target_audience = "Optimized for muscle building and athletic performance"
        else:
            target_audience = "Balanced approach for sustainable healthy living"
        
        ax.text(0.5, 0.15, target_audience,
                fontsize=20, color=self.colors['primary'],
                ha='center', va='center', weight='400')
        
        plt.tight_layout(pad=0)
        return fig
    
    def create_week_table_frame(self, week_num: int, week_data: Dict) -> plt.Figure:
        """Create full week table view"""
        fig, ax = plt.subplots(figsize=(self.width/self.dpi, self.height/self.dpi),
                               facecolor=self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # Header
        ax.text(0.5, 0.94, f"WEEK {week_num} MEAL PLAN",
                fontsize=42, color=self.colors['primary'],
                ha='center', va='top', weight='200')
        
        # Week stats
        total_calories = sum(day['totals']['calories'] for day in week_data.values())
        avg_calories = total_calories / 7
        accuracy = max(0, 100 - abs(avg_calories - self.preferences['calories']) / 
                      self.preferences['calories'] * 100)
        
        # Stats bar
        stats_text = f"Average: {avg_calories:.0f} cal/day • Accuracy: {accuracy:.0f}%"
        ax.text(0.5, 0.88, stats_text,
                fontsize=16, color=self.colors['secondary'],
                ha='center', va='top')
        
        # Table setup
        table_top = 0.82
        table_height = 0.65
        row_height = table_height / 8  # 7 days + header
        
        # Column positions
        cols = {
            'day': (0.05, 0.12),
            'breakfast': (0.18, 0.18),
            'lunch': (0.37, 0.18),
            'dinner': (0.56, 0.18),
            'snacks': (0.75, 0.12),
            'total': (0.88, 0.08)
        }
        
        # Table header background
        header_rect = FancyBboxPatch((0.04, table_top - row_height), 0.92, row_height,
                                   boxstyle="round,pad=0.01",
                                   facecolor=self.colors['table_header'],
                                   edgecolor='none',
                                   alpha=0.9)
        ax.add_patch(header_rect)
        
        # Headers
        y_header = table_top - row_height/2
        for col, (x, width) in cols.items():
            if col == 'day':
                text = 'DAY'
            elif col == 'total':
                text = 'TOTAL'
            else:
                text = col.upper()
            
            ax.text(x + width/2, y_header, text,
                    fontsize=14, color='white',
                    ha='center', va='center', weight='600')
        
        # Table rows
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for i, day_name in enumerate(days):
            y_row = table_top - (i + 2) * row_height
            
            # Alternating row backgrounds
            if i % 2 == 0:
                row_rect = Rectangle((0.04, y_row), 0.92, row_height,
                                   facecolor=self.colors['table_row2'],
                                   edgecolor='none', alpha=0.5)
                ax.add_patch(row_rect)
            
            # Day name
            ax.text(cols['day'][0] + 0.01, y_row + row_height/2, 
                    day_name[:3].upper(),
                    fontsize=14, color=self.colors['primary'],
                    ha='left', va='center', weight='500')
            
            # Meals
            day_data = week_data[day_name]
            meals = day_data['meals']
            
            # Breakfast
            breakfast = next((m for k, m in meals.items() if 'breakfast' in k), None)
            if breakfast:
                ax.text(cols['breakfast'][0] + 0.01, y_row + row_height/2,
                        breakfast['name'][:20] + '...' if len(breakfast['name']) > 20 else breakfast['name'],
                        fontsize=11, color=self.colors['primary'],
                        ha='left', va='center')
                ax.text(cols['breakfast'][0] + cols['breakfast'][1] - 0.01, y_row + row_height/2,
                        f"{breakfast['calories']:.0f}",
                        fontsize=10, color=self.colors['secondary'],
                        ha='right', va='center')
            
            # Lunch
            lunch = next((m for k, m in meals.items() if 'lunch' in k), None)
            if lunch:
                ax.text(cols['lunch'][0] + 0.01, y_row + row_height/2,
                        lunch['name'][:20] + '...' if len(lunch['name']) > 20 else lunch['name'],
                        fontsize=11, color=self.colors['primary'],
                        ha='left', va='center')
                ax.text(cols['lunch'][0] + cols['lunch'][1] - 0.01, y_row + row_height/2,
                        f"{lunch['calories']:.0f}",
                        fontsize=10, color=self.colors['secondary'],
                        ha='right', va='center')
            
            # Dinner
            dinner = next((m for k, m in meals.items() if 'dinner' in k), None)
            if dinner:
                ax.text(cols['dinner'][0] + 0.01, y_row + row_height/2,
                        dinner['name'][:20] + '...' if len(dinner['name']) > 20 else dinner['name'],
                        fontsize=11, color=self.colors['primary'],
                        ha='left', va='center')
                ax.text(cols['dinner'][0] + cols['dinner'][1] - 0.01, y_row + row_height/2,
                        f"{dinner['calories']:.0f}",
                        fontsize=10, color=self.colors['secondary'],
                        ha='right', va='center')
            
            # Snacks count
            snack_count = len([k for k in meals.keys() if 'snack' in k])
            if snack_count > 0:
                ax.text(cols['snacks'][0] + cols['snacks'][1]/2, y_row + row_height/2,
                        f"{snack_count} snack{'s' if snack_count > 1 else ''}",
                        fontsize=11, color=self.colors['secondary'],
                        ha='center', va='center')
            
            # Total calories with color coding
            total_cal = day_data['totals']['calories']
            cal_diff = abs(total_cal - self.preferences['calories'])
            if cal_diff <= 50:
                cal_color = self.colors['success']
            elif cal_diff <= 100:
                cal_color = self.colors['primary']
            else:
                cal_color = self.colors['warning']
            
            ax.text(cols['total'][0] + cols['total'][1]/2, y_row + row_height/2,
                    f"{total_cal:.0f}",
                    fontsize=12, color=cal_color,
                    ha='center', va='center', weight='600')
        
        # Footer note
        ax.text(0.5, 0.05, "Detailed daily breakdowns follow",
                fontsize=14, color=self.colors['secondary'],
                ha='center', va='center', style='italic')
        
        plt.tight_layout(pad=0)
        return fig
    
    def create_day_detail_frame(self, week_num: int, day_name: str, 
                               day_num: int, day_data: Dict) -> plt.Figure:
        """Create detailed daily view with all meals and quantities"""
        fig, ax = plt.subplots(figsize=(self.width/self.dpi, self.height/self.dpi),
                               facecolor=self.colors['background'])
        ax.set_facecolor(self.colors['background'])
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # Header with day number
        ax.text(0.5, 0.93, f"DAY {day_num} • {day_name.upper()}",
                fontsize=36, color=self.colors['primary'],
                ha='center', va='top', weight='300')
        
        ax.text(0.5, 0.88, f"Week {week_num}",
                fontsize=18, color=self.colors['secondary'],
                ha='center', va='top')
        
        # Day totals with visual elements
        totals = day_data['totals']
        
        # Create macro summary box
        box_y = 0.78
        box_height = 0.08
        summary_box = FancyBboxPatch((0.15, box_y), 0.7, box_height,
                                   boxstyle="round,pad=0.02",
                                   facecolor=self.colors['light_gray'],
                                   edgecolor=self.colors['secondary'],
                                   linewidth=1, alpha=0.8)
        ax.add_patch(summary_box)
        
        # Daily summary inside box
        ax.text(0.5, box_y + box_height/2, 
                f"{totals['calories']:.0f} calories • "
                f"Protein {totals['protein']:.0f}g • "
                f"Fat {totals['fat']:.0f}g • "
                f"Carbs {totals['carbs']:.0f}g",
                fontsize=20, color=self.colors['primary'],
                ha='center', va='center', weight='500')
        
        # Meals detail
        y_pos = 0.65
        meal_spacing = 0.15
        
        # Determine meal order
        meal_order = ['breakfast', 'lunch', 'dinner', 'snack']
        sorted_meals = []
        
        for meal_type in meal_order:
            for meal_name, meal_data in day_data['meals'].items():
                if meal_type in meal_name.lower():
                    sorted_meals.append((meal_name, meal_data))
        
        for meal_name, meal in sorted_meals:
            # Meal section background
            meal_rect = FancyBboxPatch((0.08, y_pos - 0.11), 0.84, 0.12,
                                     boxstyle="round,pad=0.01",
                                     facecolor='white',
                                     edgecolor=self.colors['light_gray'],
                                     linewidth=1)
            ax.add_patch(meal_rect)
            
            # Meal type and name
            meal_label = meal_name.replace('_', ' ').title()
            ax.text(0.1, y_pos, meal_label.upper(),
                    fontsize=12, color=self.colors['accent'],
                    ha='left', va='top', weight='700')
            
            ax.text(0.1, y_pos - 0.025, meal['name'],
                    fontsize=18, color=self.colors['primary'],
                    ha='left', va='top', weight='500')
            
            # Calories badge on right
            cal_badge = FancyBboxPatch((0.8, y_pos - 0.03), 0.1, 0.035,
                                     boxstyle="round,pad=0.01",
                                     facecolor=self.colors['accent'],
                                     edgecolor='none', alpha=0.9)
            ax.add_patch(cal_badge)
            
            ax.text(0.85, y_pos - 0.0125, f"{meal['calories']:.0f} cal",
                    fontsize=14, color='white',
                    ha='center', va='center', weight='600')
            
            # Ingredients in two columns
            ingredients = meal['ingredients']
            num_ingredients = len(ingredients)
            col1_items = ingredients[:num_ingredients//2 + num_ingredients%2]
            col2_items = ingredients[num_ingredients//2 + num_ingredients%2:]
            
            # Column 1
            ing_y = y_pos - 0.05
            for ing in col1_items:
                ing_text = f"• {ing['item']}: {ing['amount']} {ing['unit']}"
                ax.text(0.12, ing_y, ing_text,
                        fontsize=11, color=self.colors['secondary'],
                        ha='left', va='top')
                ing_y -= 0.018
            
            # Column 2
            ing_y = y_pos - 0.05
            for ing in col2_items:
                ing_text = f"• {ing['item']}: {ing['amount']} {ing['unit']}"
                ax.text(0.5, ing_y, ing_text,
                        fontsize=11, color=self.colors['secondary'],
                        ha='left', va='top')
                ing_y -= 0.018
            
            # Prep time if available
            if 'prep_time' in meal:
                ax.text(0.1, y_pos - 0.095, f"⏱ {meal['prep_time']} min",
                        fontsize=10, color=self.colors['accent'],
                        ha='left', va='top', style='italic')
            
            y_pos -= meal_spacing
        
        plt.tight_layout(pad=0)
        return fig
    
    def create_report_frame(self) -> plt.Figure:
        """Create comprehensive report with charts and graphs"""
        fig = plt.figure(figsize=(self.width/self.dpi, self.height/self.dpi),
                        facecolor=self.colors['background'])
        
        # Create grid for subplots
        gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.3,
                             left=0.08, right=0.92, top=0.88, bottom=0.08)
        
        # Title
        fig.text(0.5, 0.94, "MEAL PLAN ANALYSIS",
                fontsize=42, color=self.colors['primary'],
                ha='center', va='top', weight='200')
        
        # 1. Calorie Accuracy Chart (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        self._create_calorie_accuracy_chart(ax1)
        
        # 2. Macro Distribution (top middle)
        ax2 = fig.add_subplot(gs[0, 1])
        self._create_macro_distribution_chart(ax2)
        
        # 3. Weekly Comparison (top right)
        ax3 = fig.add_subplot(gs[0, 2])
        self._create_weekly_comparison(ax3)
        
        # 4. Daily Calorie Trend (middle span)
        ax4 = fig.add_subplot(gs[1, :])
        self._create_daily_trend_chart(ax4)
        
        # 5. Meal Type Distribution (bottom left)
        ax5 = fig.add_subplot(gs[2, 0])
        self._create_meal_distribution_chart(ax5)
        
        # 6. Accuracy Score Gauge (bottom middle)
        ax6 = fig.add_subplot(gs[2, 1])
        self._create_accuracy_gauge(ax6)
        
        # 7. Key Metrics (bottom right)
        ax7 = fig.add_subplot(gs[2, 2])
        self._create_key_metrics(ax7)
        
        return fig
    
    def _create_calorie_accuracy_chart(self, ax):
        """Create calorie accuracy visualization"""
        ax.set_title("Calorie Accuracy", fontsize=16, color=self.colors['primary'], 
                     weight='500', pad=10)
        
        # Calculate accuracy for each day
        accuracies = []
        days = []
        
        for week_key in ['week1', 'week2']:
            for day, data in self.plan[week_key].items():
                total_cal = data['totals']['calories']
                accuracy = max(0, 100 - abs(total_cal - self.preferences['calories']) / 
                              self.preferences['calories'] * 100)
                accuracies.append(accuracy)
                days.append(day[:3])
        
        # Create bar chart
        x = range(len(accuracies))
        colors = [self.colors['success'] if acc >= 98 else 
                 self.colors['warning'] if acc >= 95 else 
                 self.colors['error'] for acc in accuracies]
        
        bars = ax.bar(x, accuracies, color=colors, alpha=0.8)
        
        # Target line
        ax.axhline(y=95, color=self.colors['secondary'], linestyle='--', 
                   linewidth=2, alpha=0.5)
        ax.text(len(x)-1, 96, 'Target', ha='right', va='bottom',
                fontsize=10, color=self.colors['secondary'])
        
        ax.set_ylim(85, 102)
        ax.set_xticks([])
        ax.set_ylabel('Accuracy %', fontsize=12, color=self.colors['secondary'])
        ax.grid(True, axis='y', alpha=0.2)
        
        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)
    
    def _create_macro_distribution_chart(self, ax):
        """Create macro distribution pie chart"""
        ax.set_title("Macro Distribution", fontsize=16, color=self.colors['primary'],
                     weight='500', pad=10)
        
        # Calculate average macros
        total_days = 0
        total_protein = total_fat = total_carbs = 0
        
        for week_key in ['week1', 'week2']:
            for day_data in self.plan[week_key].values():
                totals = day_data['totals']
                total_protein += totals['protein']
                total_fat += totals['fat']
                total_carbs += totals['carbs']
                total_days += 1
        
        avg_protein = total_protein / total_days
        avg_fat = total_fat / total_days
        avg_carbs = total_carbs / total_days
        
        # Calculate percentages
        total_cal = (avg_protein * 4) + (avg_fat * 9) + (avg_carbs * 4)
        sizes = [
            (avg_protein * 4) / total_cal * 100,
            (avg_fat * 9) / total_cal * 100,
            (avg_carbs * 4) / total_cal * 100
        ]
        
        colors = [self.colors['success'], self.colors['warning'], self.colors['accent']]
        labels = ['Protein', 'Fat', 'Carbs']
        
        # Create donut chart
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors,
                                          autopct='%1.0f%%', startangle=90,
                                          textprops={'fontsize': 12})
        
        # Create center circle for donut effect
        centre_circle = Circle((0, 0), 0.70, fc='white')
        ax.add_artist(centre_circle)
        
        ax.axis('equal')
    
    def _create_weekly_comparison(self, ax):
        """Create week 1 vs week 2 comparison"""
        ax.set_title("Weekly Comparison", fontsize=16, color=self.colors['primary'],
                     weight='500', pad=10)
        
        # Calculate weekly averages
        week_data = []
        for week_key in ['week1', 'week2']:
            total_cal = sum(day['totals']['calories'] for day in self.plan[week_key].values())
            avg_cal = total_cal / 7
            
            total_protein = sum(day['totals']['protein'] for day in self.plan[week_key].values())
            avg_protein = total_protein / 7
            
            week_data.append({
                'calories': avg_cal,
                'protein': avg_protein,
                'accuracy': max(0, 100 - abs(avg_cal - self.preferences['calories']) / 
                              self.preferences['calories'] * 100)
            })
        
        # Create comparison bars
        categories = ['Calories', 'Protein (g)', 'Accuracy %']
        week1_values = [week_data[0]['calories'], week_data[0]['protein'], week_data[0]['accuracy']]
        week2_values = [week_data[1]['calories'], week_data[1]['protein'], week_data[1]['accuracy']]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, week1_values, width, label='Week 1',
                       color=self.colors['primary'], alpha=0.8)
        bars2 = ax.bar(x + width/2, week2_values, width, label='Week 2',
                       color=self.colors['accent'], alpha=0.8)
        
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=10)
        ax.legend(fontsize=10)
        ax.grid(True, axis='y', alpha=0.2)
        
        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)
    
    def _create_daily_trend_chart(self, ax):
        """Create 14-day calorie trend line"""
        ax.set_title("14-Day Calorie Trend", fontsize=16, color=self.colors['primary'],
                     weight='500', pad=10)
        
        # Collect daily data
        daily_calories = []
        days = []
        day_count = 0
        
        for week_key in ['week1', 'week2']:
            for day, data in self.plan[week_key].items():
                daily_calories.append(data['totals']['calories'])
                day_count += 1
                days.append(f"D{day_count}")
        
        # Create line chart
        x = range(len(daily_calories))
        ax.plot(x, daily_calories, color=self.colors['primary'], 
                linewidth=3, marker='o', markersize=8, alpha=0.8)
        
        # Target line
        target = [self.preferences['calories']] * len(daily_calories)
        ax.plot(x, target, color=self.colors['accent'], 
                linestyle='--', linewidth=2, alpha=0.6)
        
        # Fill between
        ax.fill_between(x, daily_calories, target, 
                       where=(np.array(daily_calories) > np.array(target)),
                       color=self.colors['warning'], alpha=0.2)
        ax.fill_between(x, daily_calories, target,
                       where=(np.array(daily_calories) <= np.array(target)),
                       color=self.colors['success'], alpha=0.2)
        
        ax.set_xticks(x[::2])
        ax.set_xticklabels(days[::2], fontsize=10)
        ax.set_ylabel('Calories', fontsize=12, color=self.colors['secondary'])
        ax.grid(True, alpha=0.2)
        
        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)
    
    def _create_meal_distribution_chart(self, ax):
        """Create meal type calorie distribution"""
        ax.set_title("Calories by Meal", fontsize=16, color=self.colors['primary'],
                     weight='500', pad=10)
        
        # Calculate average calories per meal type
        meal_totals = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0}
        meal_counts = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0}
        
        for week_key in ['week1', 'week2']:
            for day_data in self.plan[week_key].values():
                for meal_name, meal_data in day_data['meals'].items():
                    for meal_type in meal_totals.keys():
                        if meal_type in meal_name.lower():
                            meal_totals[meal_type] += meal_data['calories']
                            meal_counts[meal_type] += 1
                            break
        
        # Calculate averages
        meal_avgs = {k: meal_totals[k] / meal_counts[k] if meal_counts[k] > 0 else 0 
                    for k in meal_totals.keys()}
        
        # Create horizontal bar chart
        meals = list(meal_avgs.keys())
        values = list(meal_avgs.values())
        colors = [self.colors['success'], self.colors['primary'], 
                 self.colors['accent'], self.colors['warning']]
        
        y_pos = np.arange(len(meals))
        bars = ax.barh(y_pos, values, color=colors, alpha=0.8)
        
        # Add value labels
        for i, (meal, value) in enumerate(zip(meals, values)):
            ax.text(value + 10, i, f'{value:.0f}', 
                   va='center', fontsize=11, color=self.colors['secondary'])
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels([m.capitalize() for m in meals], fontsize=12)
        ax.set_xlabel('Average Calories', fontsize=11, color=self.colors['secondary'])
        ax.grid(True, axis='x', alpha=0.2)
        
        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)
    
    def _create_accuracy_gauge(self, ax):
        """Create overall accuracy gauge"""
        ax.set_title("Overall Accuracy", fontsize=16, color=self.colors['primary'],
                     weight='500', pad=10)
        
        # Calculate overall accuracy
        val1 = self.plan['validation']['week1']['overall_score']
        val2 = self.plan['validation']['week2']['overall_score']
        overall_score = (val1 + val2) / 2
        
        # Create semi-circular gauge
        theta = np.linspace(np.pi, 0, 100)
        r_inner = 0.6
        r_outer = 1.0
        
        # Background arc
        for i in range(len(theta)-1):
            t1, t2 = theta[i], theta[i+1]
            
            if i < 33:
                color = self.colors['error']
            elif i < 66:
                color = self.colors['warning']
            else:
                color = self.colors['success']
            
            vertices = [
                (r_inner * np.cos(t1), r_inner * np.sin(t1)),
                (r_outer * np.cos(t1), r_outer * np.sin(t1)),
                (r_outer * np.cos(t2), r_outer * np.sin(t2)),
                (r_inner * np.cos(t2), r_inner * np.sin(t2))
            ]
            poly = patches.Polygon(vertices, facecolor=color, alpha=0.3)
            ax.add_patch(poly)
        
        # Score indicator
        score_angle = np.pi - (overall_score / 100 * np.pi)
        ax.plot([0, 0.8 * np.cos(score_angle)], [0, 0.8 * np.sin(score_angle)],
                color=self.colors['primary'], linewidth=4)
        
        # Center circle
        circle = Circle((0, 0), 0.5, facecolor='white', edgecolor=self.colors['primary'], 
                       linewidth=2)
        ax.add_patch(circle)
        
        # Score text
        ax.text(0, -0.1, f"{overall_score:.0f}%",
                fontsize=32, color=self.colors['primary'],
                ha='center', va='center', weight='600')
        
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-0.3, 1.2)
        ax.axis('off')
    
    def _create_key_metrics(self, ax):
        """Create key metrics summary"""
        ax.set_title("Key Metrics", fontsize=16, color=self.colors['primary'],
                     weight='500', pad=10)
        ax.axis('off')
        
        # Calculate metrics
        total_meals = sum(len(day['meals']) for week in ['week1', 'week2'] 
                         for day in self.plan[week].values())
        
        # Count unique meals
        unique_meals = set()
        for week_key in ['week1', 'week2']:
            for day_data in self.plan[week_key].values():
                for meal_data in day_data['meals'].values():
                    unique_meals.add(meal_data['name'])
        
        # Cuisine variety if tracked
        cuisines = set()
        for week_key in ['week1', 'week2']:
            for day_data in self.plan[week_key].values():
                for meal_data in day_data['meals'].values():
                    if 'cuisine' in meal_data:
                        cuisines.add(meal_data['cuisine'])
        
        metrics = [
            ("Total Meals", str(total_meals)),
            ("Unique Recipes", str(len(unique_meals))),
            ("Cuisine Variety", str(len(cuisines)) if cuisines else "N/A"),
            ("Avg Daily Error", f"{abs(self.preferences['calories'] - sum(day['totals']['calories'] for week in ['week1', 'week2'] for day in self.plan[week].values()) / 14):.0f} cal")
        ]
        
        y_pos = 0.8
        for label, value in metrics:
            ax.text(0.1, y_pos, label, fontsize=13, color=self.colors['secondary'])
            ax.text(0.9, y_pos, value, fontsize=13, color=self.colors['primary'],
                   ha='right', weight='600')
            y_pos -= 0.25
    
    def create_video(self, output_path: str = 'meal_plan_video.mp4'):
        """Generate the complete video with transitions"""
        print("\n🎬 Creating enhanced meal plan video...")
        print("-" * 30)
        
        # Create frames directory
        os.makedirs('video_frames', exist_ok=True)
        
        frame_files = []
        frame_count = 0
        all_frame_paths = []  # Store paths for transitions
        
        # Helper function to save frame
        def save_frame(fig, frame_num):
            frame_file = f'video_frames/frame_{frame_num:04d}.png'
            fig.savefig(frame_file, dpi=self.dpi, bbox_inches='tight', pad_inches=0,
                        facecolor=self.colors['background'], edgecolor='none')
            plt.close(fig)
            return frame_file
        
        # 1. Title frame
        print("Creating title frame...")
        fig = self.create_title_frame()
        frame_path = save_frame(fig, frame_count)
        all_frame_paths.append(frame_path)
        frame_count += 1
        
        # 2. Summary frame
        print("Creating summary frame...")
        fig = self.create_summary_frame()
        frame_path = save_frame(fig, frame_count)
        all_frame_paths.append(frame_path)
        frame_count += 1
        
        # 3. Week 1 table
        print("Creating Week 1 table...")
        fig = self.create_week_table_frame(1, self.plan['week1'])
        frame_path = save_frame(fig, frame_count)
        all_frame_paths.append(frame_path)
        frame_count += 1
        
        # 4. Week 2 table
        print("Creating Week 2 table...")
        fig = self.create_week_table_frame(2, self.plan['week2'])
        frame_path = save_frame(fig, frame_count)
        all_frame_paths.append(frame_path)
        frame_count += 1
        
        # 5. Daily details
        day_counter = 0
        for week_num, week_key in enumerate(['week1', 'week2'], 1):
            for day_name, day_data in self.plan[week_key].items():
                day_counter += 1
                print(f"Creating Day {day_counter} detail...")
                fig = self.create_day_detail_frame(week_num, day_name, day_counter, day_data)
                frame_path = save_frame(fig, frame_count)
                all_frame_paths.append(frame_path)
                frame_count += 1
        
        # 6. Report frame
        print("Creating analysis report...")
        fig = self.create_report_frame()
        frame_path = save_frame(fig, frame_count)
        all_frame_paths.append(frame_path)
        frame_count += 1
        
        # Now compile video with transitions
        print("\nCompiling video with transitions...")
        
        # Read first frame to get dimensions
        first_frame = cv2.imread(all_frame_paths[0])
        if first_frame is None:
            print(f"ERROR: Could not read first frame")
            return
        
        height, width, _ = first_frame.shape
        print(f"Video resolution: {width}x{height}")
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (width, height))
        
        if not out.isOpened():
            print("ERROR: Could not open video writer")
            return
        
        # Process frames with transitions
        frame_durations = [
            self.title_duration,
            self.summary_duration,
            self.week_table_duration,
            self.week_table_duration,
        ] + [self.day_detail_duration] * 14 + [self.report_duration]
        
        total_frames_written = 0
        
        for i, (frame_path, duration) in enumerate(zip(all_frame_paths, frame_durations)):
            # Write main frames
            frame = cv2.imread(frame_path)
            
            # Add transition at the beginning (except for first frame)
            if i > 0:
                prev_frame_path = all_frame_paths[i-1]
                transition_frames = self.create_transition(prev_frame_path, frame_path)
                for trans_frame in transition_frames:
                    out.write(trans_frame)
                    total_frames_written += 1
            
            # Write the main frame for its duration
            for _ in range(int(self.fps * duration)):
                out.write(frame)
                total_frames_written += 1
            
            # Progress update
            if i % 5 == 0:
                print(f"Progress: {i+1}/{len(all_frame_paths)} frames processed")
        
        # Release video writer
        out.release()
        cv2.destroyAllWindows()
        
        # Cleanup
        print("\nCleaning up temporary files...")
        for frame_path in all_frame_paths:
            try:
                os.remove(frame_path)
            except Exception as e:
                print(f"Could not remove {frame_path}: {e}")
        
        try:
            os.rmdir('video_frames')
        except:
            pass
        
        print(f"\n✅ Video created successfully: {output_path}")
        print(f"   Total frames: {total_frames_written}")
        print(f"   Duration: {total_frames_written / self.fps:.1f} seconds")
        print(f"   Resolution: {width}x{height}")
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024*1024)
            print(f"   File size: {file_size:.1f} MB")


# Standalone execution
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎥 ENHANCED MEAL PLAN VIDEO GENERATOR")
    print("="*60)
    
    # Check if meal plan exists
    import os
    if not os.path.exists('meal_plan.json'):
        print("\n❌ No meal plan found!")
        print("Please run meal_optimizer.py first to generate a meal plan.")
        exit(1)
    
    # Load meal plan
    print("\nLoading meal plan...")
    with open('meal_plan.json', 'r') as f:
        meal_plan = json.load(f)
    
    # Generate video
    generator = VideoGenerator(meal_plan)
    
    print("\nSELECT VIDEO TYPE:")
    print("[1] Legacy Style (Educational)")
    print("[2] Cibozer Style (Tech/Algorithm Focus)")
    print("[3] Both")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == "1":
        output_name = input("\nEnter output filename (default: meal_plan_video.mp4): ").strip()
        if not output_name:
            output_name = "meal_plan_video.mp4"
        
        if not output_name.endswith('.mp4'):
            output_name += '.mp4'
        
        generator.create_video(output_name)
        
    elif choice == "2":
        generator.create_cibozer_version()
        
    elif choice == "3":
        # Legacy video
        print("\nGenerating legacy video...")
        generator.create_video("meal_plan_legacy.mp4")
        
        # Cibozer videos
        print("\nGenerating Cibozer videos...")
        generator.create_cibozer_version()
        
    print("\n🎬 Video generation complete!")


# Add this function at the END of the file
def generate_videos_from_meal_plans():
    """Generate videos for all meal plans in the meal_plans directory"""
    import glob
    import json
    import os
    from datetime import datetime
    
    # Create output directory
    os.makedirs("meal_videos", exist_ok=True)
    
    # Find all meal plan JSON files
    meal_plan_files = glob.glob("meal_plans/*.json")
    
    if not meal_plan_files:
        print("❌ No meal plan files found in meal_plans directory!")
        return
    
    print(f"\n🎥 Found {len(meal_plan_files)} meal plans to process")
    print("\nSELECT VIDEO STYLE:")
    print("[1] Legacy Style (Educational)")
    print("[2] Cibozer Style (Tech/Algorithm)")
    print("[3] Both")
    
    style_choice = input("\nChoice (1-3): ").strip()
    
    processed = 0
    failed = 0
    skipped = 0
    
    for i, plan_file in enumerate(meal_plan_files, 1):
        # Extract filename without extension
        base_name = os.path.basename(plan_file).replace('.json', '')
        
        if style_choice in ["1", "3"]:
            video_file = f"meal_videos/{base_name}_legacy.mp4"
            
            # Skip if video already exists
            if os.path.exists(video_file):
                print(f"[{i}/{len(meal_plan_files)}] Skipping existing: {video_file}")
                skipped += 1
            else:
                try:
                    # Load meal plan
                    print(f"\n[{i}/{len(meal_plan_files)}] Processing (Legacy): {plan_file}")
                    with open(plan_file, 'r', encoding='utf-8') as f:
                        meal_plan = json.load(f)
                    
                    # Create video generator
                    generator = VideoGenerator(meal_plan)
                    
                    # Generate video
                    generator.create_video(video_file)
                    
                    processed += 1
                    print(f"✅ Created: {video_file}")
                    
                except Exception as e:
                    failed += 1
                    print(f"❌ Failed to create video for {plan_file}: {e}")
        
        if style_choice in ["2", "3"]:
            try:
                # Load meal plan
                print(f"\n[{i}/{len(meal_plan_files)}] Processing (Cibozer): {plan_file}")
                with open(plan_file, 'r', encoding='utf-8') as f:
                    meal_plan = json.load(f)
                
                # Create video generator
                generator = VideoGenerator(meal_plan)
                
                # Generate Cibozer version
                generator.create_cibozer_version(f"./cibozer_output/{base_name}")
                
                processed += 1
                print(f"✅ Created Cibozer videos")
                
            except Exception as e:
                failed += 1
                print(f"❌ Failed to create Cibozer video for {plan_file}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("🎬 VIDEO GENERATION COMPLETE")
    print("="*60)
    print(f"Total files: {len(meal_plan_files)}")
    print(f"Processed: {processed}")
    print(f"Skipped (existing): {skipped}")
    print(f"Failed: {failed}")
    
    if style_choice in ["1", "3"]:
        print(f"\nLegacy videos saved in: meal_videos/")
    if style_choice in ["2", "3"]:
        print(f"Cibozer videos saved in: cibozer_output/")
    
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")