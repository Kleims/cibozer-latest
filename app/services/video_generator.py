"""Video generation service for meal plans."""
import os
import tempfile
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from flask import current_app


class VideoGenerator:
    """Service for generating videos from meal plans."""
    
    # Platform specifications
    PLATFORM_SPECS = {
        'youtube': {
            'width': 1920,
            'height': 1080,
            'fps': 30,
            'duration': 60,  # seconds
            'format': 'mp4'
        },
        'youtube_shorts': {
            'width': 1080,
            'height': 1920,
            'fps': 30,
            'duration': 60,
            'format': 'mp4'
        },
        'tiktok': {
            'width': 1080,
            'height': 1920,
            'fps': 30,
            'duration': 60,
            'format': 'mp4'
        },
        'instagram': {
            'width': 1080,
            'height': 1080,
            'fps': 30,
            'duration': 60,
            'format': 'mp4'
        },
        'instagram_reels': {
            'width': 1080,
            'height': 1920,
            'fps': 30,
            'duration': 90,
            'format': 'mp4'
        }
    }
    
    def __init__(self):
        self.output_dir = current_app.config.get('VIDEO_OUTPUT_DIR', 'static/videos')
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Ensure output directory exists."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def generate_meal_plan_video(
        self,
        meal_plan: Dict[str, Any],
        platform: str = 'youtube',
        style: str = 'modern',
        music: bool = True,
        voiceover: bool = False
    ) -> str:
        """
        Generate a video from a meal plan.
        
        Args:
            meal_plan: Dictionary containing meal plan data
            platform: Target platform (youtube, tiktok, instagram, etc.)
            style: Visual style (modern, classic, minimalist)
            music: Whether to include background music
            voiceover: Whether to include AI voiceover
            
        Returns:
            URL/path to the generated video file
        """
        try:
            # Validate platform
            if platform not in self.PLATFORM_SPECS:
                platform = 'youtube'
            
            specs = self.PLATFORM_SPECS[platform]
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"meal_plan_{platform}_{timestamp}.{specs['format']}"
            output_path = os.path.join(self.output_dir, filename)
            
            # Prepare video data
            video_data = self._prepare_video_data(meal_plan, platform)
            
            # Generate video (placeholder for actual implementation)
            # In production, this would call actual video generation service
            self._generate_video_file(
                video_data,
                output_path,
                specs,
                style=style,
                music=music,
                voiceover=voiceover
            )
            
            # Return relative URL
            video_url = f"/static/videos/{filename}"
            
            current_app.logger.info(f"Video generated successfully: {video_url}")
            return video_url
            
        except Exception as e:
            current_app.logger.error(f"Error generating video: {str(e)}")
            raise
    
    def _prepare_video_data(self, meal_plan: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Prepare meal plan data for video generation."""
        video_data = {
            'title': meal_plan.get('title', 'My Meal Plan'),
            'platform': platform,
            'scenes': []
        }
        
        # Add intro scene
        video_data['scenes'].append({
            'type': 'intro',
            'duration': 3,
            'title': video_data['title'],
            'subtitle': f"{meal_plan.get('diet_type', 'Custom')} Diet Plan"
        })
        
        # Add summary scene
        if 'summary' in meal_plan:
            summary = meal_plan['summary']
            video_data['scenes'].append({
                'type': 'summary',
                'duration': 5,
                'data': {
                    'total_days': summary.get('total_days', 0),
                    'total_calories': summary.get('average_daily_calories', 0),
                    'diet_type': meal_plan.get('diet_type', 'standard')
                }
            })
        
        # Add meal scenes
        for day_data in meal_plan.get('days', [])[:3]:  # Limit to first 3 days for video
            for meal in day_data.get('meals', []):
                scene = {
                    'type': 'meal',
                    'duration': 4,
                    'meal_name': meal.get('name', 'Meal'),
                    'meal_type': meal.get('type', 'meal'),
                    'calories': meal.get('calories', 0),
                    'ingredients': meal.get('ingredients', [])[:5],  # Top 5 ingredients
                    'image': self._get_meal_image(meal)
                }
                video_data['scenes'].append(scene)
        
        # Add outro scene
        video_data['scenes'].append({
            'type': 'outro',
            'duration': 3,
            'call_to_action': 'Start your healthy journey today!'
        })
        
        return video_data
    
    def _generate_video_file(
        self,
        video_data: Dict[str, Any],
        output_path: str,
        specs: Dict[str, Any],
        style: str = 'modern',
        music: bool = True,
        voiceover: bool = False
    ):
        """
        Generate the actual video file.
        
        In production, this would:
        1. Create video frames using a library like OpenCV or MoviePy
        2. Add text overlays and transitions
        3. Include background music if requested
        4. Add AI voiceover if requested
        5. Export in the correct format and specifications
        """
        # Placeholder implementation
        # In production, integrate with actual video generation library
        
        # For now, create a placeholder file
        with open(output_path, 'w') as f:
            f.write("PLACEHOLDER VIDEO FILE\n")
            f.write(json.dumps(video_data, indent=2))
        
        current_app.logger.info(f"Video file created at: {output_path}")
    
    def _get_meal_image(self, meal: Dict[str, Any]) -> Optional[str]:
        """Get or generate an image for a meal."""
        # In production, this could:
        # 1. Use a pre-existing image database
        # 2. Generate images using AI (DALL-E, Stable Diffusion)
        # 3. Use stock photos based on meal type
        return None
    
    def generate_recipe_video(
        self,
        recipe: Dict[str, Any],
        platform: str = 'youtube',
        style: str = 'step-by-step'
    ) -> str:
        """Generate a video for a single recipe."""
        # Implementation for single recipe video
        pass
    
    def generate_social_media_clips(
        self,
        meal_plan: Dict[str, Any],
        platforms: List[str] = None
    ) -> Dict[str, str]:
        """Generate multiple video clips for different social media platforms."""
        if platforms is None:
            platforms = ['youtube_shorts', 'tiktok', 'instagram_reels']
        
        clips = {}
        for platform in platforms:
            try:
                video_url = self.generate_meal_plan_video(
                    meal_plan,
                    platform=platform,
                    style='social',
                    music=True,
                    voiceover=False
                )
                clips[platform] = video_url
            except Exception as e:
                current_app.logger.error(f"Failed to generate {platform} clip: {str(e)}")
                clips[platform] = None
        
        return clips
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Get the status of a video generation job."""
        # In production, this would check async job status
        return {
            'id': video_id,
            'status': 'completed',
            'progress': 100,
            'url': f"/static/videos/{video_id}.mp4"
        }
    
    def cleanup_old_videos(self, days: int = 7):
        """Clean up videos older than specified days."""
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        for file_path in Path(self.output_dir).glob('*.mp4'):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    current_app.logger.info(f"Deleted old video: {file_path}")
                except Exception as e:
                    current_app.logger.error(f"Failed to delete video {file_path}: {str(e)}")