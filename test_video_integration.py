"""
Simplified integration tests for video generation
Focus on core functionality that can be reliably tested
"""

import pytest
import os
import tempfile
from video_service import VideoService
from simple_video_generator import SimpleVideoGenerator


class TestVideoServiceCore:
    """Test core video service functionality"""
    
    @pytest.fixture
    def video_service(self, tmp_path):
        """Create a VideoService instance with temp directory"""
        return VideoService(videos_dir=str(tmp_path / "videos"), upload_enabled=False)
    
    @pytest.fixture
    def sample_meal_plan(self):
        """Sample meal plan for testing"""
        return {
            'meals': {
                'breakfast': {
                    'name': 'Test Breakfast',
                    'calories': 400,
                    'protein': 30,
                    'carbs': 40,
                    'fat': 15,
                    'ingredients': [
                        {'item': 'eggs', 'amount': 2, 'unit': 'whole'},
                        {'item': 'oats', 'amount': 50, 'unit': 'g'}
                    ]
                }
            },
            'totals': {
                'calories': 400,
                'protein': 30,
                'carbs': 40,
                'fat': 15
            }
        }
    
    def test_video_service_initialization(self, tmp_path):
        """Test video service initializes correctly"""
        video_service = VideoService(videos_dir=str(tmp_path / "videos"), upload_enabled=False)
        
        assert video_service.videos_dir == str(tmp_path / "videos")
        assert video_service.upload_enabled is False
        assert video_service.video_generator is not None
        assert video_service.uploader is None  # Since upload_enabled=False
        assert os.path.exists(video_service.videos_dir)
    
    def test_platform_info(self, video_service):
        """Test getting platform information"""
        info = video_service.get_platform_info()
        
        assert 'supported_platforms' in info
        assert 'enabled_platforms' in info
        assert 'platform_specs' in info
        assert 'available_voices' in info
        assert 'upload_enabled' in info
        
        # Check standard platforms
        assert 'youtube_shorts' in info['supported_platforms']
        assert 'tiktok' in info['supported_platforms']
        assert 'instagram_feed' in info['supported_platforms']
    
    def test_platform_enable_disable(self, video_service):
        """Test enabling and disabling platforms"""
        # Check initial state
        assert video_service.enabled_platforms['youtube_shorts'] is True
        
        # Disable platform
        video_service.disable_platform('youtube_shorts')
        assert video_service.enabled_platforms['youtube_shorts'] is False
        
        # Re-enable platform
        video_service.enable_platform('youtube_shorts')
        assert video_service.enabled_platforms['youtube_shorts'] is True
    
    def test_video_stats_empty(self, video_service):
        """Test video statistics with no videos"""
        stats = video_service.get_video_stats()
        
        assert stats['total_videos'] == 0
        assert stats['videos_by_platform'] == {}
        assert stats['total_size_mb'] == 0
        assert stats['oldest_video'] is None
        assert stats['newest_video'] is None
    
    def test_video_stats_with_files(self, video_service, tmp_path):
        """Test video statistics with dummy files"""
        # Create dummy video files
        videos_dir = tmp_path / "videos"
        videos_dir.mkdir(exist_ok=True)
        
        for i in range(3):
            video_file = videos_dir / f"youtube_shorts_{i}.mp4"
            video_file.write_bytes(b"dummy" * 1000)
        
        stats = video_service.get_video_stats()
        
        assert stats['total_videos'] == 3
        assert stats['total_size_mb'] > 0
        assert 'youtube' in stats['videos_by_platform']
        assert stats['videos_by_platform']['youtube'] == 3
    
    @pytest.mark.asyncio
    async def test_voice_generation(self, video_service):
        """Test voice generation creates audio file"""
        test_text = "Testing voice generation"
        audio_path = await video_service.test_voice_generation(test_text)
        
        assert audio_path is not None
        assert os.path.exists(audio_path)
        assert audio_path.endswith('.mp3')
    
    @pytest.mark.asyncio
    async def test_video_generation_single_platform(self, video_service, sample_meal_plan):
        """Test generating video for single platform"""
        result = await video_service.generate_single_platform_video(
            sample_meal_plan,
            'youtube_shorts',
            auto_upload=False
        )
        
        assert 'generation' in result
        assert 'youtube_shorts' in result['generation']
        assert result['generation']['youtube_shorts']['status'] == 'success'
        assert 'video_path' in result['generation']['youtube_shorts']
        
        # Check video file exists
        video_path = result['generation']['youtube_shorts']['video_path']
        assert os.path.exists(video_path)
        assert video_path.endswith('.mp4')
    
    def test_cleanup_old_videos(self, video_service, tmp_path):
        """Test cleanup of old video files"""
        videos_dir = tmp_path / "videos" 
        videos_dir.mkdir(exist_ok=True)
        
        # Create test video file
        old_video = videos_dir / "old_video.mp4"
        old_video.write_bytes(b"old content")
        
        # Make it appear old by modifying timestamp
        import time
        old_time = time.time() - (8 * 24 * 60 * 60)  # 8 days ago
        os.utime(old_video, (old_time, old_time))
        
        # Run cleanup
        video_service.cleanup_old_videos(days_old=7)
        
        # Check file was deleted
        assert not old_video.exists()


class TestSimpleVideoGenerator:
    """Test the SimpleVideoGenerator directly"""
    
    @pytest.fixture
    def video_generator(self, tmp_path):
        """Create a SimpleVideoGenerator instance"""
        return SimpleVideoGenerator(output_dir=str(tmp_path / "videos"))
    
    def test_generator_initialization(self, video_generator, tmp_path):
        """Test video generator initializes correctly"""
        assert video_generator.output_dir == str(tmp_path / "videos")
        assert os.path.exists(video_generator.output_dir)
        assert 'youtube_shorts' in video_generator.PLATFORM_SPECS
    
    def test_platform_specs(self, video_generator):
        """Test platform specifications"""
        specs = video_generator.PLATFORM_SPECS
        
        # Check YouTube Shorts spec
        assert specs['youtube_shorts']['resolution'] == (1080, 1920)
        assert specs['youtube_shorts']['fps'] == 30
        assert specs['youtube_shorts']['format'] == 'mp4'
        
        # Check TikTok spec
        assert specs['tiktok']['resolution'] == (1080, 1920)
        
        # Check Instagram spec
        assert specs['instagram_feed']['resolution'] == (1080, 1080)
    
    @pytest.mark.asyncio
    async def test_speech_generation(self, video_generator):
        """Test speech generation"""
        text = "Test speech generation"
        audio_path = await video_generator.generate_speech(text)
        
        assert audio_path is not None
        assert os.path.exists(audio_path)
        assert audio_path.endswith('.mp3')
    
    @pytest.mark.asyncio
    async def test_video_generation_creates_file(self, video_generator):
        """Test that video generation creates a file"""
        meal_plan = {
            'meals': {
                'breakfast': {
                    'name': 'Simple Breakfast',
                    'calories': 300,
                    'protein': 20,
                    'carbs': 30,
                    'fat': 10,
                    'ingredients': [
                        {'item': 'eggs', 'amount': 2, 'unit': 'whole'}
                    ]
                }
            },
            'totals': {'calories': 300, 'protein': 20, 'carbs': 30, 'fat': 10}
        }
        
        video_path = await video_generator.generate_video(meal_plan, 'youtube_shorts')
        
        assert video_path is not None
        assert os.path.exists(video_path)
        assert video_path.endswith('.mp4')
        assert 'youtube_shorts' in video_path


if __name__ == '__main__':
    pytest.main([__file__, '-v'])