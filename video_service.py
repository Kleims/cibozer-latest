"""
Integrated Video Service
Combines video generation and social media uploading with Edge TTS Christopher voice
"""

import asyncio
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from simple_video_generator import SimpleVideoGenerator
from social_media_uploader import SocialMediaUploader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoService:
    """
    Integrated service for video generation and social media uploading
    """
    
    def __init__(self, videos_dir: str = "videos", upload_enabled: bool = True):
        """
        Initialize the video service
        
        Args:
            videos_dir: Directory to store generated videos
            upload_enabled: Whether to enable automatic uploads
        """
        self.videos_dir = videos_dir
        self.upload_enabled = upload_enabled
        
        # Initialize components
        self.video_generator = SimpleVideoGenerator(videos_dir)
        self.uploader = SocialMediaUploader() if upload_enabled else None
        
        # Create necessary directories
        os.makedirs(videos_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Set up file logging
        log_file = os.path.join("logs", f"video_service_{datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Platform configurations
        self.enabled_platforms = {
            'youtube_shorts': True,
            'youtube_long': True,
            'tiktok': True,
            'instagram_feed': True,
            'facebook': True
        }
    
    async def generate_and_upload_videos(self, 
                                       meal_plan: Dict, 
                                       platforms: List[str] = None,
                                       voice: str = 'christopher',
                                       auto_upload: bool = True) -> Dict[str, Dict]:
        """
        Generate videos for specified platforms and optionally upload them
        
        Args:
            meal_plan: Meal plan data
            platforms: List of platforms to generate for (None = all enabled)
            voice: Voice to use for TTS
            auto_upload: Whether to automatically upload generated videos
            
        Returns:
            Dictionary containing generation and upload results
        """
        if platforms is None:
            platforms = [p for p, enabled in self.enabled_platforms.items() if enabled]
        
        logger.info(f"Starting video generation for platforms: {platforms}")
        
        # Generate videos
        generation_results = {}
        for platform in platforms:
            try:
                logger.info(f"Generating video for {platform}")
                video_path = await self.video_generator.generate_video(meal_plan, platform)
                generation_results[platform] = {
                    'status': 'success',
                    'video_path': video_path,
                    'error': None
                }
                logger.info(f"[SUCCESS] {platform} video generated: {video_path}")
            except Exception as e:
                logger.error(f"[FAILED] {platform} video generation failed: {e}")
                generation_results[platform] = {
                    'status': 'error',
                    'video_path': None,
                    'error': str(e)
                }
        
        # Upload videos if enabled
        upload_results = {}
        if auto_upload and self.upload_enabled and self.uploader:
            logger.info("Starting video uploads")
            
            # Extract successful video paths
            video_paths = {
                platform: result['video_path'] 
                for platform, result in generation_results.items() 
                if result['status'] == 'success' and result['video_path']
            }
            
            if video_paths:
                upload_results = await self.uploader.upload_to_all_platforms(video_paths, meal_plan)
                
                # Log upload results
                for platform, url in upload_results.items():
                    if url:
                        logger.info(f"[SUCCESS] {platform} upload successful: {url}")
                    else:
                        logger.error(f"[FAILED] {platform} upload failed")
        
        # Combine results
        results = {
            'generation': generation_results,
            'upload': upload_results,
            'summary': self._create_summary(generation_results, upload_results)
        }
        
        # Save results to file
        self._save_results(results, meal_plan)
        
        return results
    
    def _create_summary(self, generation_results: Dict, upload_results: Dict) -> Dict:
        """
        Create a summary of results
        """
        total_platforms = len(generation_results)
        successful_generations = sum(1 for r in generation_results.values() if r['status'] == 'success')
        successful_uploads = sum(1 for url in upload_results.values() if url is not None)
        
        return {
            'total_platforms': total_platforms,
            'successful_generations': successful_generations,
            'successful_uploads': successful_uploads,
            'generation_success_rate': (successful_generations / total_platforms * 100) if total_platforms > 0 else 0,
            'upload_success_rate': (successful_uploads / len(upload_results) * 100) if upload_results else 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def _save_results(self, results: Dict, meal_plan: Dict):
        """
        Save results to JSON file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join("logs", f"video_results_{timestamp}.json")
        
        # Include meal plan in results for reference
        results['meal_plan'] = meal_plan
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Results saved to: {results_file}")
    
    async def generate_single_platform_video(self, 
                                           meal_plan: Dict, 
                                           platform: str,
                                           voice: str = 'christopher',
                                           auto_upload: bool = True) -> Dict:
        """
        Generate and optionally upload video for a single platform
        
        Args:
            meal_plan: Meal plan data
            platform: Platform to generate for
            voice: Voice to use for TTS
            auto_upload: Whether to automatically upload
            
        Returns:
            Dictionary containing generation and upload results
        """
        return await self.generate_and_upload_videos(
            meal_plan, 
            platforms=[platform], 
            voice=voice, 
            auto_upload=auto_upload
        )
    
    def get_platform_info(self) -> Dict:
        """
        Get information about supported platforms
        """
        return {
            'supported_platforms': list(self.video_generator.PLATFORM_SPECS.keys()),
            'enabled_platforms': [p for p, enabled in self.enabled_platforms.items() if enabled],
            'platform_specs': self.video_generator.PLATFORM_SPECS,
            'available_voices': ['christopher', 'aria', 'guy', 'jenny'],
            'upload_enabled': self.upload_enabled
        }
    
    def enable_platform(self, platform: str):
        """Enable a platform for video generation"""
        if platform in self.video_generator.PLATFORM_SPECS:
            self.enabled_platforms[platform] = True
            logger.info(f"Enabled platform: {platform}")
        else:
            logger.warning(f"Unknown platform: {platform}")
    
    def disable_platform(self, platform: str):
        """Disable a platform for video generation"""
        if platform in self.enabled_platforms:
            self.enabled_platforms[platform] = False
            logger.info(f"Disabled platform: {platform}")
        else:
            logger.warning(f"Unknown platform: {platform}")
    
    async def test_voice_generation(self, text: str = "Hello! This is a test of Edge TTS Christopher voice.") -> str:
        """
        Test voice generation with Christopher voice
        
        Args:
            text: Test text to speak
            
        Returns:
            Path to generated audio file
        """
        try:
            audio_path = await self.video_generator.generate_speech(text)
            logger.info(f"[SUCCESS] Voice test successful: {audio_path}")
            return audio_path
        except Exception as e:
            logger.error(f"[FAILED] Voice test failed: {e}")
            raise
    
    async def test_video_generation(self, test_meal_plan: Dict = None) -> str:
        """
        Test video generation with a sample meal plan
        
        Args:
            test_meal_plan: Optional test meal plan data
            
        Returns:
            Path to generated test video
        """
        if test_meal_plan is None:
            test_meal_plan = {
                'meals': {
                    'breakfast': {
                        'name': 'Test Breakfast',
                        'calories': 350,
                        'protein': 25,
                        'carbs': 30,
                        'fat': 12,
                        'ingredients': [
                            {'item': 'eggs', 'amount': 2, 'unit': 'whole'},
                            {'item': 'oats', 'amount': 50, 'unit': 'g'}
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
        
        try:
            video_path = await self.video_generator.generate_video(test_meal_plan, 'youtube_shorts')
            logger.info(f"[SUCCESS] Video test successful: {video_path}")
            return video_path
        except Exception as e:
            logger.error(f"[FAILED] Video test failed: {e}")
            raise
    
    def get_video_stats(self) -> Dict:
        """
        Get statistics about generated videos
        """
        stats = {
            'total_videos': 0,
            'videos_by_platform': {},
            'total_size_mb': 0,
            'oldest_video': None,
            'newest_video': None
        }
        
        if not os.path.exists(self.videos_dir):
            return stats
        
        video_files = [f for f in os.listdir(self.videos_dir) if f.endswith('.mp4')]
        stats['total_videos'] = len(video_files)
        
        for video_file in video_files:
            # Extract platform from filename
            platform = video_file.split('_')[0]
            stats['videos_by_platform'][platform] = stats['videos_by_platform'].get(platform, 0) + 1
            
            # Get file size
            file_path = os.path.join(self.videos_dir, video_file)
            stats['total_size_mb'] += os.path.getsize(file_path) / (1024 * 1024)
            
            # Get file dates
            mtime = os.path.getmtime(file_path)
            if stats['oldest_video'] is None or mtime < stats['oldest_video']:
                stats['oldest_video'] = mtime
            if stats['newest_video'] is None or mtime > stats['newest_video']:
                stats['newest_video'] = mtime
        
        # Convert timestamps to readable format
        if stats['oldest_video']:
            stats['oldest_video'] = datetime.fromtimestamp(stats['oldest_video']).isoformat()
        if stats['newest_video']:
            stats['newest_video'] = datetime.fromtimestamp(stats['newest_video']).isoformat()
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        
        return stats
    
    def cleanup_old_videos(self, days_old: int = 7):
        """
        Clean up videos older than specified days
        
        Args:
            days_old: Number of days after which to delete videos
        """
        if not os.path.exists(self.videos_dir):
            return
        
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        deleted_count = 0
        
        for video_file in os.listdir(self.videos_dir):
            if video_file.endswith('.mp4'):
                file_path = os.path.join(self.videos_dir, video_file)
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    deleted_count += 1
                    logger.info(f"Deleted old video: {video_file}")
        
        logger.info(f"Cleanup completed. Deleted {deleted_count} old videos.")

# Flask integration
def create_video_service_for_flask(app):
    """
    Create and configure video service for Flask app
    """
    video_service = VideoService()
    app.video_service = video_service
    
    @app.route('/api/video/generate', methods=['POST'])
    async def generate_video():
        """API endpoint to generate videos"""
        try:
            from flask import request, jsonify
            
            data = request.get_json()
            meal_plan = data.get('meal_plan')
            platforms = data.get('platforms', ['youtube_shorts'])
            voice = data.get('voice', 'christopher')
            auto_upload = data.get('auto_upload', False)
            
            if not meal_plan:
                return jsonify({'error': 'No meal plan provided'}), 400
            
            results = await video_service.generate_and_upload_videos(
                meal_plan, platforms, voice, auto_upload
            )
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Video generation API error: {e}")
            return jsonify({
                'error': 'Failed to generate videos',
                'details': str(e)
            }), 500
    
    @app.route('/api/video/platforms', methods=['GET'])
    def get_platforms():
        """API endpoint to get platform information"""
        return jsonify(video_service.get_platform_info())
    
    @app.route('/api/video/stats', methods=['GET'])
    def get_video_stats():
        """API endpoint to get video statistics"""
        return jsonify(video_service.get_video_stats())
    
    return video_service

# Example usage
async def main():
    """
    Example usage of the video service
    """
    # Create video service
    video_service = VideoService(upload_enabled=False)  # Disable uploads for testing
    
    # Test meal plan
    test_meal_plan = {
        'meals': {
            'breakfast': {
                'name': 'Power Breakfast',
                'calories': 450,
                'protein': 30,
                'carbs': 35,
                'fat': 18,
                'ingredients': [
                    {'item': 'eggs', 'amount': 3, 'unit': 'whole'},
                    {'item': 'oats', 'amount': 60, 'unit': 'g'},
                    {'item': 'blueberries', 'amount': 100, 'unit': 'g'},
                    {'item': 'almonds', 'amount': 20, 'unit': 'g'}
                ]
            },
            'lunch': {
                'name': 'Mediterranean Bowl',
                'calories': 520,
                'protein': 35,
                'carbs': 40,
                'fat': 25,
                'ingredients': [
                    {'item': 'chicken_breast', 'amount': 150, 'unit': 'g'},
                    {'item': 'quinoa', 'amount': 80, 'unit': 'g'},
                    {'item': 'olive_oil', 'amount': 15, 'unit': 'ml'},
                    {'item': 'feta_cheese', 'amount': 50, 'unit': 'g'}
                ]
            }
        },
        'totals': {
            'calories': 970,
            'protein': 65,
            'carbs': 75,
            'fat': 43
        }
    }
    
    # Show platform info
    print("=== Platform Information ===")
    platform_info = video_service.get_platform_info()
    for key, value in platform_info.items():
        print(f"{key}: {value}")
    
    # Test voice generation
    print("\n=== Testing Voice Generation ===")
    try:
        audio_path = await video_service.test_voice_generation()
        print(f"✓ Voice test successful: {audio_path}")
    except Exception as e:
        print(f"✗ Voice test failed: {e}")
    
    # Test video generation for YouTube Shorts
    print("\n=== Testing Video Generation ===")
    try:
        results = await video_service.generate_single_platform_video(
            test_meal_plan, 
            'youtube_shorts', 
            voice='christopher',
            auto_upload=False
        )
        print(f"✓ Video generation test successful")
        print(f"Results: {results['summary']}")
    except Exception as e:
        print(f"✗ Video generation test failed: {e}")
    
    # Show video stats
    print("\n=== Video Statistics ===")
    stats = video_service.get_video_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())