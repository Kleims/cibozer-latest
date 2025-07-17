"""
Multi-Platform Video Generator with Edge TTS Christopher Voice
Generates videos for Facebook, Instagram, TikTok, YouTube Shorts, and YouTube Long-form
"""

import asyncio
import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_agg import FigureCanvasAgg
import seaborn as sns
import edge_tts
import tempfile
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import moviepy as mp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlatformVideoGenerator:
    """
    Generates videos optimized for different social media platforms
    """
    
    # Platform specifications
    PLATFORM_SPECS = {
        'youtube_shorts': {
            'resolution': (1080, 1920),  # 9:16 aspect ratio
            'duration': 60,
            'fps': 30,
            'bitrate': '5M',
            'format': 'mp4'
        },
        'youtube_long': {
            'resolution': (1920, 1080),  # 16:9 aspect ratio
            'duration': 300,  # 5 minutes
            'fps': 30,
            'bitrate': '8M',
            'format': 'mp4'
        },
        'tiktok': {
            'resolution': (1080, 1920),  # 9:16 aspect ratio
            'duration': 60,
            'fps': 30,
            'bitrate': '5M',
            'format': 'mp4'
        },
        'instagram_feed': {
            'resolution': (1080, 1080),  # 1:1 aspect ratio
            'duration': 60,
            'fps': 30,
            'bitrate': '5M',
            'format': 'mp4'
        },
        'instagram_story': {
            'resolution': (1080, 1920),  # 9:16 aspect ratio
            'duration': 15,
            'fps': 30,
            'bitrate': '5M',
            'format': 'mp4'
        },
        'facebook': {
            'resolution': (1920, 1080),  # 16:9 aspect ratio
            'duration': 120,
            'fps': 30,
            'bitrate': '8M',
            'format': 'mp4'
        }
    }
    
    def __init__(self, output_dir: str = "videos"):
        """Initialize the video generator"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Color schemes for different platforms
        self.color_schemes = {
            'youtube_shorts': {
                'primary': '#FF0000',
                'secondary': '#282828',
                'accent': '#FFFFFF',
                'background': '#0F0F0F'
            },
            'tiktok': {
                'primary': '#FF0050',
                'secondary': '#25F4EE',
                'accent': '#FFFFFF',
                'background': '#000000'
            },
            'instagram_feed': {
                'primary': '#E4405F',
                'secondary': '#405DE6',
                'accent': '#FFFFFF',
                'background': '#FAFAFA'
            },
            'facebook': {
                'primary': '#1877F2',
                'secondary': '#42B883',
                'accent': '#FFFFFF',
                'background': '#F0F2F5'
            }
        }
        
        # Available voices (Christopher is the main one)
        self.voices = {
            'christopher': 'en-US-ChristopherNeural',
            'aria': 'en-US-AriaNeural',
            'guy': 'en-US-GuyNeural',
            'jenny': 'en-US-JennyNeural'
        }
        
        self.default_voice = 'christopher'
        
    async def generate_speech(self, text: str, voice: str = None, output_path: str = None) -> str:
        """
        Generate speech using Edge TTS with Christopher voice
        """
        if voice is None:
            voice = self.default_voice
            
        voice_name = self.voices.get(voice, self.voices['christopher'])
        
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
        
        # Create Edge TTS communicate object
        communicate = edge_tts.Communicate(text, voice_name)
        
        # Generate speech
        await communicate.save(output_path)
        
        logger.info(f"Generated speech with {voice_name}: {output_path}")
        return output_path
    
    def create_nutrition_chart(self, meal_data: Dict, platform: str, size: Tuple[int, int]) -> np.ndarray:
        """
        Create a nutrition chart visualization
        """
        # Set up the figure with platform-specific styling
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(size[0]/100, size[1]/100), dpi=100)
        
        colors = self.color_schemes.get(platform, self.color_schemes['youtube_shorts'])
        
        # Macronutrient pie chart
        macros = ['Protein', 'Carbs', 'Fat']
        macro_values = [
            meal_data.get('protein', 0),
            meal_data.get('carbs', 0),
            meal_data.get('fat', 0)
        ]
        
        colors_pie = [colors['primary'], colors['secondary'], colors['accent']]
        
        wedges, texts, autotexts = ax1.pie(macro_values, labels=macros, autopct='%1.1f%%', 
                                          colors=colors_pie, startangle=90)
        ax1.set_title('Macronutrients', fontsize=16, fontweight='bold', color='white')
        
        # Calorie bar chart
        calories = meal_data.get('calories', 0)
        target_calories = 2000  # Default target
        
        ax2.bar(['Calories'], [calories], color=colors['primary'], alpha=0.8)
        ax2.axhline(y=target_calories, color=colors['accent'], linestyle='--', alpha=0.7)
        ax2.set_ylabel('Calories', fontsize=12, color='white')
        ax2.set_title('Calorie Content', fontsize=16, fontweight='bold', color='white')
        ax2.tick_params(colors='white')
        
        # Style the figure
        fig.patch.set_facecolor(colors['background'])
        for ax in [ax1, ax2]:
            ax.set_facecolor(colors['background'])
            ax.tick_params(colors='white')
        
        plt.tight_layout()
        
        # Convert to numpy array
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        buf = canvas.buffer_rgba()
        chart_array = np.asarray(buf).reshape(fig.canvas.get_width_height()[::-1] + (4,))
        
        plt.close(fig)
        
        return chart_array[:, :, :3]  # Remove alpha channel
    
    def create_ingredient_slide(self, ingredients: List[Dict], platform: str, size: Tuple[int, int]) -> np.ndarray:
        """
        Create a slide showing ingredients list
        """
        img = Image.new('RGB', size, color=self.color_schemes[platform]['background'])
        draw = ImageDraw.Draw(img)
        
        # Try to load a font, fallback to default
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            item_font = ImageFont.truetype("arial.ttf", 40)
        except:
            title_font = ImageFont.load_default()
            item_font = ImageFont.load_default()
        
        # Draw title
        title = "Ingredients"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (size[0] - title_width) // 2
        draw.text((title_x, 50), title, fill=self.color_schemes[platform]['primary'], font=title_font)
        
        # Draw ingredients list
        y_offset = 150
        for i, ingredient in enumerate(ingredients[:10]):  # Limit to 10 ingredients
            name = ingredient.get('item', '').replace('_', ' ').title()
            amount = ingredient.get('amount', 0)
            unit = ingredient.get('unit', 'g')
            
            text = f"• {name}: {amount}{unit}"
            draw.text((50, y_offset), text, fill=self.color_schemes[platform]['accent'], font=item_font)
            y_offset += 60
        
        return np.array(img)
    
    def create_title_slide(self, title: str, subtitle: str, platform: str, size: Tuple[int, int]) -> np.ndarray:
        """
        Create a title slide
        """
        img = Image.new('RGB', size, color=self.color_schemes[platform]['background'])
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 80)
            subtitle_font = ImageFont.truetype("arial.ttf", 50)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Draw title
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (size[0] - title_width) // 2
        title_y = size[1] // 2 - 100
        draw.text((title_x, title_y), title, fill=self.color_schemes[platform]['primary'], font=title_font)
        
        # Draw subtitle
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (size[0] - subtitle_width) // 2
        subtitle_y = title_y + 120
        draw.text((subtitle_x, subtitle_y), subtitle, fill=self.color_schemes[platform]['accent'], font=subtitle_font)
        
        return np.array(img)
    
    def create_meal_slide(self, meal: Dict, platform: str, size: Tuple[int, int]) -> np.ndarray:
        """
        Create a slide for a single meal
        """
        img = Image.new('RGB', size, color=self.color_schemes[platform]['background'])
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            info_font = ImageFont.truetype("arial.ttf", 40)
        except:
            title_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Draw meal name
        meal_name = meal.get('name', 'Meal').replace('_', ' ').title()
        name_bbox = draw.textbbox((0, 0), meal_name, font=title_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_x = (size[0] - name_width) // 2
        draw.text((name_x, 50), meal_name, fill=self.color_schemes[platform]['primary'], font=title_font)
        
        # Draw nutrition info
        y_offset = 150
        nutrition_info = [
            f"Calories: {meal.get('calories', 0)}",
            f"Protein: {meal.get('protein', 0)}g",
            f"Carbs: {meal.get('carbs', 0)}g",
            f"Fat: {meal.get('fat', 0)}g"
        ]
        
        for info in nutrition_info:
            info_bbox = draw.textbbox((0, 0), info, font=info_font)
            info_width = info_bbox[2] - info_bbox[0]
            info_x = (size[0] - info_width) // 2
            draw.text((info_x, y_offset), info, fill=self.color_schemes[platform]['accent'], font=info_font)
            y_offset += 80
        
        return np.array(img)
    
    async def generate_video(self, meal_plan: Dict, platform: str, voice: str = None) -> str:
        """
        Generate a complete video for the specified platform
        """
        logger.info(f"Generating video for {platform}")
        
        if platform not in self.PLATFORM_SPECS:
            raise ValueError(f"Unsupported platform: {platform}")
        
        spec = self.PLATFORM_SPECS[platform]
        size = spec['resolution']
        fps = spec['fps']
        max_duration = spec['duration']
        
        # Create output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{platform}_{timestamp}.{spec['format']}"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Generate script text
        script_text = self.generate_script(meal_plan, platform)
        
        # Generate TTS audio
        audio_path = await self.generate_speech(script_text, voice)
        
        # Load audio to get duration
        audio_clip = mp.AudioFileClip(audio_path)
        actual_duration = min(audio_clip.duration, max_duration)
        
        # Create video frames
        frames = []
        total_frames = int(actual_duration * fps)
        
        # Generate different slide types
        meals = meal_plan.get('meals', {})
        
        # Title slide (first 2 seconds)
        title_slide = self.create_title_slide(
            "AI Meal Plan", 
            f"{len(meals)} Delicious Meals", 
            platform, 
            size
        )
        title_frames = int(2 * fps)
        frames.extend([title_slide] * title_frames)
        
        # Meal slides
        remaining_frames = total_frames - len(frames)
        frames_per_meal = remaining_frames // len(meals) if meals else remaining_frames
        
        for meal_name, meal_data in meals.items():
            # Meal info slide
            meal_slide = self.create_meal_slide(meal_data, platform, size)
            frames.extend([meal_slide] * (frames_per_meal // 2))
            
            # Ingredients slide
            ingredients = meal_data.get('ingredients', [])
            if ingredients:
                ingredient_slide = self.create_ingredient_slide(ingredients, platform, size)
                frames.extend([ingredient_slide] * (frames_per_meal // 2))
        
        # Pad frames to match audio duration
        while len(frames) < total_frames:
            frames.append(frames[-1])
        
        frames = frames[:total_frames]
        
        # Create video clip
        video_clip = mp.ImageSequenceClip(frames, fps=fps)
        
        # Add audio
        final_clip = video_clip.set_audio(audio_clip.subclip(0, actual_duration))
        
        # Write video file
        final_clip.write_videofile(
            output_path,
            fps=fps,
            codec='libx264',
            bitrate=spec['bitrate'],
            audio_codec='aac',
            temp_audiofile=f"{output_path}.temp.wav",
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        # Cleanup
        final_clip.close()
        audio_clip.close()
        os.remove(audio_path)
        
        logger.info(f"Video generated: {output_path}")
        return output_path
    
    def generate_script(self, meal_plan: Dict, platform: str) -> str:
        """
        Generate script text for TTS based on meal plan and platform
        """
        meals = meal_plan.get('meals', {})
        totals = meal_plan.get('totals', {})
        
        if platform in ['youtube_shorts', 'tiktok', 'instagram_story']:
            # Short format script
            script = f"Here's your perfect AI-generated meal plan! "
            script += f"We've got {len(meals)} amazing meals with {totals.get('calories', 0)} total calories. "
            
            for meal_name, meal_data in list(meals.items())[:2]:  # Limit to 2 meals for short format
                name = meal_name.replace('_', ' ').title()
                script += f"{name} has {meal_data.get('calories', 0)} calories. "
            
            script += "Follow for more AI meal plans! Like if this helped you!"
            
        else:
            # Long format script
            script = f"Welcome to your personalized AI meal plan! "
            script += f"Today we have {len(meals)} carefully crafted meals totaling {totals.get('calories', 0)} calories. "
            
            for meal_name, meal_data in meals.items():
                name = meal_name.replace('_', ' ').title()
                script += f"For {name}, we have {meal_data.get('calories', 0)} calories, "
                script += f"{meal_data.get('protein', 0)} grams of protein, "
                script += f"{meal_data.get('carbs', 0)} grams of carbs, "
                script += f"and {meal_data.get('fat', 0)} grams of fat. "
                
                ingredients = meal_data.get('ingredients', [])[:3]  # Top 3 ingredients
                if ingredients:
                    script += "Key ingredients include "
                    script += ", ".join([ing.get('item', '').replace('_', ' ') for ing in ingredients])
                    script += ". "
            
            script += "This meal plan is optimized for your nutritional needs using advanced AI algorithms. "
            script += "Subscribe for more personalized meal plans and nutrition content!"
        
        return script
    
    async def generate_all_platforms(self, meal_plan: Dict, voice: str = None) -> Dict[str, str]:
        """
        Generate videos for all platforms
        """
        results = {}
        
        for platform in self.PLATFORM_SPECS.keys():
            try:
                video_path = await self.generate_video(meal_plan, platform, voice)
                results[platform] = video_path
                logger.info(f"✓ Generated {platform} video: {video_path}")
            except Exception as e:
                logger.error(f"✗ Failed to generate {platform} video: {e}")
                results[platform] = None
        
        return results

# Example usage and testing
async def main():
    """
    Example usage of the video generator
    """
    # Sample meal plan data
    sample_meal_plan = {
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
            },
            'lunch': {
                'name': 'Grilled Chicken Salad',
                'calories': 450,
                'protein': 35,
                'carbs': 20,
                'fat': 25,
                'ingredients': [
                    {'item': 'chicken_breast', 'amount': 150, 'unit': 'g'},
                    {'item': 'lettuce', 'amount': 100, 'unit': 'g'},
                    {'item': 'olive_oil', 'amount': 15, 'unit': 'ml'}
                ]
            }
        },
        'totals': {
            'calories': 800,
            'protein': 60,
            'carbs': 50,
            'fat': 37
        }
    }
    
    # Create generator
    generator = PlatformVideoGenerator()
    
    # Generate videos for all platforms
    results = await generator.generate_all_platforms(sample_meal_plan, voice='christopher')
    
    print("\n=== Video Generation Results ===")
    for platform, path in results.items():
        status = "✓ SUCCESS" if path else "✗ FAILED"
        print(f"{platform}: {status}")
        if path:
            print(f"  -> {path}")

if __name__ == "__main__":
    asyncio.run(main())