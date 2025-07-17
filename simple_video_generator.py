"""
Simplified Video Generator using Edge TTS Christopher Voice
Creates videos for multiple platforms without heavy dependencies
"""

import asyncio
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import edge_tts
import tempfile
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleVideoGenerator:
    """
    Simplified video generator for multiple platforms
    """
    
    PLATFORM_SPECS = {
        'youtube_shorts': {
            'resolution': (1080, 1920),  # 9:16 aspect ratio
            'duration': 60,
            'fps': 30,
            'format': 'mp4'
        },
        'youtube_long': {
            'resolution': (1920, 1080),  # 16:9 aspect ratio
            'duration': 120,  # 2 minutes for demo
            'fps': 30,
            'format': 'mp4'
        },
        'tiktok': {
            'resolution': (1080, 1920),  # 9:16 aspect ratio
            'duration': 60,
            'fps': 30,
            'format': 'mp4'
        },
        'instagram_feed': {
            'resolution': (1080, 1080),  # 1:1 aspect ratio
            'duration': 60,
            'fps': 30,
            'format': 'mp4'
        },
        'facebook': {
            'resolution': (1920, 1080),  # 16:9 aspect ratio
            'duration': 90,
            'fps': 30,
            'format': 'mp4'
        }
    }
    
    def __init__(self, output_dir: str = "videos"):
        """Initialize the video generator"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Color schemes
        self.color_schemes = {
            'youtube_shorts': {
                'primary': (255, 0, 0),     # Red
                'secondary': (40, 40, 40),  # Dark gray
                'accent': (255, 255, 255),  # White
                'background': (15, 15, 15)  # Very dark gray
            },
            'tiktok': {
                'primary': (255, 0, 80),    # Pink
                'secondary': (37, 244, 238), # Cyan
                'accent': (255, 255, 255),  # White
                'background': (0, 0, 0)     # Black
            },
            'instagram_feed': {
                'primary': (228, 64, 95),   # Instagram pink
                'secondary': (64, 93, 230), # Instagram blue
                'accent': (255, 255, 255),  # White
                'background': (250, 250, 250) # Light gray
            },
            'facebook': {
                'primary': (24, 119, 242),  # Facebook blue
                'secondary': (66, 184, 131), # Green
                'accent': (255, 255, 255),  # White
                'background': (240, 242, 245) # Light blue-gray
            }
        }
        
        # Default to all platforms
        for platform in self.PLATFORM_SPECS.keys():
            if platform not in self.color_schemes:
                self.color_schemes[platform] = self.color_schemes['youtube_shorts']
    
    async def generate_speech(self, text: str, output_path: str = None) -> str:
        """Generate speech using Edge TTS Christopher voice"""
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
        
        # Create Edge TTS communicate object
        communicate = edge_tts.Communicate(text, 'en-US-ChristopherNeural')
        
        # Generate speech
        await communicate.save(output_path)
        
        logger.info(f"Generated speech: {output_path}")
        return output_path
    
    def create_text_image(self, text: str, size: Tuple[int, int], platform: str, 
                         font_size: int = 60, centered: bool = True) -> np.ndarray:
        """Create an image with text"""
        colors = self.color_schemes[platform]
        
        # Create image
        img = Image.new('RGB', size, color=colors['background'])
        draw = ImageDraw.Draw(img)
        
        # Try to load font
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        if centered:
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
        else:
            x = 50
            y = 50
        
        # Draw text
        draw.text((x, y), text, fill=colors['accent'], font=font)
        
        return np.array(img)
    
    def create_meal_info_image(self, meal_data: Dict, size: Tuple[int, int], platform: str) -> np.ndarray:
        """Create an image showing meal information"""
        colors = self.color_schemes[platform]
        
        # Create image
        img = Image.new('RGB', size, color=colors['background'])
        draw = ImageDraw.Draw(img)
        
        # Fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 50)
            info_font = ImageFont.truetype("arial.ttf", 35)
        except:
            title_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Draw meal name
        meal_name = meal_data.get('name', 'Meal').replace('_', ' ').title()
        bbox = draw.textbbox((0, 0), meal_name, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (size[0] - text_width) // 2
        draw.text((x, 100), meal_name, fill=colors['primary'], font=title_font)
        
        # Draw nutrition info
        y_offset = 200
        nutrition_info = [
            f"Calories: {meal_data.get('calories', 0)}",
            f"Protein: {meal_data.get('protein', 0)}g",
            f"Carbs: {meal_data.get('carbs', 0)}g",
            f"Fat: {meal_data.get('fat', 0)}g"
        ]
        
        for info in nutrition_info:
            bbox = draw.textbbox((0, 0), info, font=info_font)
            text_width = bbox[2] - bbox[0]
            x = (size[0] - text_width) // 2
            draw.text((x, y_offset), info, fill=colors['accent'], font=info_font)
            y_offset += 60
        
        return np.array(img)
    
    def create_ingredients_image(self, ingredients: List[Dict], size: Tuple[int, int], platform: str) -> np.ndarray:
        """Create an image showing ingredients"""
        colors = self.color_schemes[platform]
        
        # Create image
        img = Image.new('RGB', size, color=colors['background'])
        draw = ImageDraw.Draw(img)
        
        # Fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 50)
            item_font = ImageFont.truetype("arial.ttf", 30)
        except:
            title_font = ImageFont.load_default()
            item_font = ImageFont.load_default()
        
        # Draw title
        title = "Ingredients"
        bbox = draw.textbbox((0, 0), title, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (size[0] - text_width) // 2
        draw.text((x, 80), title, fill=colors['primary'], font=title_font)
        
        # Draw ingredients
        y_offset = 160
        for ingredient in ingredients[:8]:  # Limit to 8 ingredients
            name = ingredient.get('item', '').replace('_', ' ').title()
            amount = ingredient.get('amount', 0)
            unit = ingredient.get('unit', 'g')
            
            text = f"• {name}: {amount}{unit}"
            draw.text((80, y_offset), text, fill=colors['accent'], font=item_font)
            y_offset += 50
        
        return np.array(img)
    
    def generate_script(self, meal_plan: Dict, platform: str) -> str:
        """Generate script for TTS"""
        meals = meal_plan.get('meals', {})
        totals = meal_plan.get('totals', {})
        
        if platform in ['youtube_shorts', 'tiktok', 'instagram_feed']:
            # Short format
            script = f"Here's your AI-powered meal plan! "
            script += f"We've got {len(meals)} delicious meals with {totals.get('calories', 0)} total calories. "
            
            for meal_name, meal_data in list(meals.items())[:2]:
                name = meal_name.replace('_', ' ').title()
                script += f"{name} has {meal_data.get('calories', 0)} calories with {meal_data.get('protein', 0)} grams of protein. "
            
            script += "Perfect for your fitness goals! Follow for more AI meal plans!"
        else:
            # Long format
            script = f"Welcome to your personalized AI meal planning experience! "
            script += f"Today I'm presenting {len(meals)} carefully optimized meals with {totals.get('calories', 0)} total calories. "
            
            for meal_name, meal_data in meals.items():
                name = meal_name.replace('_', ' ').title()
                script += f"Let's start with {name}. This meal provides {meal_data.get('calories', 0)} calories, "
                script += f"{meal_data.get('protein', 0)} grams of protein, "
                script += f"{meal_data.get('carbs', 0)} grams of carbs, "
                script += f"and {meal_data.get('fat', 0)} grams of healthy fats. "
            
            script += "This meal plan is scientifically designed using advanced AI algorithms to meet your specific nutritional needs. "
            script += "Subscribe and hit the notification bell for more personalized nutrition content!"
        
        return script
    
    async def create_video_opencv(self, meal_plan: Dict, platform: str) -> str:
        """Create video using OpenCV"""
        spec = self.PLATFORM_SPECS[platform]
        size = spec['resolution']
        fps = spec['fps']
        max_duration = spec['duration']
        
        # Generate script and audio
        script = self.generate_script(meal_plan, platform)
        audio_path = await self.generate_speech(script)
        
        # Create output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(self.output_dir, f"{platform}_{timestamp}.mp4")
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, size)
        
        # Generate frames
        meals = meal_plan.get('meals', {})
        total_frames = min(fps * max_duration, fps * 30)  # Cap at 30 seconds for demo
        
        frames_per_section = total_frames // (len(meals) + 1) if meals else total_frames
        
        # Title frame
        title_img = self.create_text_image(
            "AI Meal Plan", 
            size, 
            platform, 
            font_size=80
        )
        
        for _ in range(frames_per_section):
            # Convert RGB to BGR for OpenCV
            bgr_img = cv2.cvtColor(title_img, cv2.COLOR_RGB2BGR)
            out.write(bgr_img)
        
        # Meal frames
        for meal_name, meal_data in meals.items():
            # Meal info frame
            meal_img = self.create_meal_info_image(meal_data, size, platform)
            
            for _ in range(frames_per_section // 2):
                bgr_img = cv2.cvtColor(meal_img, cv2.COLOR_RGB2BGR)
                out.write(bgr_img)
            
            # Ingredients frame
            ingredients = meal_data.get('ingredients', [])
            if ingredients:
                ingredients_img = self.create_ingredients_image(ingredients, size, platform)
                
                for _ in range(frames_per_section // 2):
                    bgr_img = cv2.cvtColor(ingredients_img, cv2.COLOR_RGB2BGR)
                    out.write(bgr_img)
        
        # Release video writer
        out.release()
        
        # Clean up audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        logger.info(f"Video created: {output_path}")
        return output_path
    
    async def generate_video(self, meal_plan: Dict, platform: str) -> str:
        """Generate video for specified platform"""
        if platform not in self.PLATFORM_SPECS:
            raise ValueError(f"Unsupported platform: {platform}")
        
        logger.info(f"Generating video for {platform}")
        
        return await self.create_video_opencv(meal_plan, platform)
    
    async def generate_all_platforms(self, meal_plan: Dict) -> Dict[str, str]:
        """Generate videos for all platforms"""
        results = {}
        
        for platform in self.PLATFORM_SPECS.keys():
            try:
                video_path = await self.generate_video(meal_plan, platform)
                results[platform] = video_path
                logger.info(f"✓ Generated {platform} video: {video_path}")
            except Exception as e:
                logger.error(f"✗ Failed to generate {platform} video: {e}")
                results[platform] = None
        
        return results

# Test the generator
async def test_generator():
    """Test the video generator"""
    generator = SimpleVideoGenerator()
    
    # Test meal plan
    test_meal_plan = {
        'meals': {
            'breakfast': {
                'name': 'Protein Pancakes',
                'calories': 350,
                'protein': 25,
                'carbs': 30,
                'fat': 12,
                'ingredients': [
                    {'item': 'eggs', 'amount': 2, 'unit': 'whole'},
                    {'item': 'oats', 'amount': 50, 'unit': 'g'},
                    {'item': 'blueberries', 'amount': 100, 'unit': 'g'}
                ]
            }
        },
        'totals': {
            'calories': 350,
            'protein': 25,
            'carbs': 30,
            'fat': 12
        }
    }
    
    # Test YouTube Shorts generation
    print("Generating YouTube Shorts video...")
    try:
        video_path = await generator.generate_video(test_meal_plan, 'youtube_shorts')
        print(f"✓ Success: {video_path}")
        
        # Check file size
        if os.path.exists(video_path):
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            print(f"File size: {size_mb:.2f} MB")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_generator())