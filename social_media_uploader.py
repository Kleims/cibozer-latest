"""
Social Media Auto-Uploader
Handles automated uploads to Facebook, Instagram, TikTok, and YouTube
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import aiohttp
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaUploader:
    """
    Handles automated uploads to various social media platforms
    """
    
    def __init__(self, credentials_file: str = "social_credentials.json"):
        """
        Initialize the uploader with API credentials
        """
        self.credentials_file = credentials_file
        self.credentials = self.load_credentials()
        
        # YouTube API scopes
        self.youtube_scopes = [
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube'
        ]
        
        # Platform-specific settings
        self.platform_settings = {
            'youtube_shorts': {
                'title_suffix': ' #Shorts',
                'description_suffix': '\n\n#Shorts #MealPlan #AI #Nutrition #HealthyEating',
                'category_id': '26',  # Howto & Style
                'tags': ['shorts', 'mealplan', 'ai', 'nutrition', 'healthy']
            },
            'youtube_long': {
                'title_suffix': ' - AI Meal Plan',
                'description_suffix': '\n\n#MealPlan #AI #Nutrition #HealthyEating #Fitness',
                'category_id': '26',  # Howto & Style
                'tags': ['mealplan', 'ai', 'nutrition', 'healthy', 'fitness']
            },
            'facebook': {
                'title_suffix': ' 🍽️',
                'description_suffix': '\n\n#MealPlan #AI #Nutrition #HealthyEating',
                'privacy': 'PUBLIC'
            },
            'instagram_feed': {
                'title_suffix': ' 📱',
                'description_suffix': '\n\n#MealPlan #AI #Nutrition #HealthyEating #InstagramReels',
                'media_type': 'REELS'
            },
            'tiktok': {
                'title_suffix': ' 🎵',
                'description_suffix': '\n\n#MealPlan #AI #Nutrition #HealthyEating #TikTok',
                'privacy_level': 'PUBLIC_TO_EVERYONE'
            }
        }
    
    def load_credentials(self) -> Dict:
        """
        Load API credentials from file
        """
        try:
            with open(self.credentials_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Credentials file {self.credentials_file} not found")
            return {}
    
    def save_credentials(self, credentials: Dict):
        """
        Save API credentials to file
        """
        with open(self.credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)
    
    def get_youtube_service(self):
        """
        Get authenticated YouTube service
        """
        creds = None
        token_file = 'youtube_token.pickle'
        
        # Load existing credentials
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # You'll need to create a client_secrets.json file from Google Cloud Console
                client_secrets_file = 'client_secrets.json'
                if not os.path.exists(client_secrets_file):
                    logger.error(f"YouTube client secrets file not found: {client_secrets_file}")
                    return None
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file, self.youtube_scopes)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('youtube', 'v3', credentials=creds)
    
    async def upload_to_youtube(self, video_path: str, platform: str, meal_plan: Dict) -> Optional[str]:
        """
        Upload video to YouTube (Shorts or Long-form)
        """
        try:
            youtube = self.get_youtube_service()
            if not youtube:
                logger.error("Failed to get YouTube service")
                return None
            
            settings = self.platform_settings[platform]
            
            # Generate title and description
            title = self.generate_title(meal_plan, platform)
            description = self.generate_description(meal_plan, platform)
            
            # Video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': settings['tags'],
                    'categoryId': settings['category_id']
                },
                'status': {
                    'privacyStatus': 'public'
                }
            }
            
            # Add shorts-specific metadata
            if platform == 'youtube_shorts':
                body['snippet']['title'] = title + settings['title_suffix']
                body['snippet']['description'] = description + settings['description_suffix']
            
            # Upload video
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            
            request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"✓ YouTube upload successful: {video_url}")
            return video_url
            
        except Exception as e:
            logger.error(f"✗ YouTube upload failed: {e}")
            return None
    
    async def upload_to_facebook(self, video_path: str, meal_plan: Dict) -> Optional[str]:
        """
        Upload video to Facebook
        """
        try:
            facebook_creds = self.credentials.get('facebook', {})
            page_access_token = facebook_creds.get('page_access_token')
            page_id = facebook_creds.get('page_id')
            
            if not page_access_token or not page_id:
                logger.error("Facebook credentials not found")
                return None
            
            # Generate title and description
            title = self.generate_title(meal_plan, 'facebook')
            description = self.generate_description(meal_plan, 'facebook')
            
            # Facebook Graph API upload
            async with aiohttp.ClientSession() as session:
                # Step 1: Initialize upload
                init_url = f"https://graph.facebook.com/v18.0/{page_id}/videos"
                init_data = {
                    'access_token': page_access_token,
                    'upload_phase': 'start',
                    'file_size': os.path.getsize(video_path)
                }
                
                async with session.post(init_url, data=init_data) as response:
                    if response.status != 200:
                        logger.error(f"Facebook upload init failed: {response.status}")
                        return None
                    
                    init_result = await response.json()
                    video_id = init_result.get('video_id')
                    upload_session_id = init_result.get('upload_session_id')
                
                # Step 2: Upload video file
                with open(video_path, 'rb') as video_file:
                    upload_url = f"https://graph.facebook.com/v18.0/{page_id}/videos"
                    upload_data = aiohttp.FormData()
                    upload_data.add_field('access_token', page_access_token)
                    upload_data.add_field('upload_phase', 'transfer')
                    upload_data.add_field('upload_session_id', upload_session_id)
                    upload_data.add_field('video_file_chunk', video_file, 
                                        filename=os.path.basename(video_path))
                    
                    async with session.post(upload_url, data=upload_data) as response:
                        if response.status != 200:
                            logger.error(f"Facebook video upload failed: {response.status}")
                            return None
                
                # Step 3: Finalize upload
                finalize_url = f"https://graph.facebook.com/v18.0/{page_id}/videos"
                finalize_data = {
                    'access_token': page_access_token,
                    'upload_phase': 'finish',
                    'upload_session_id': upload_session_id,
                    'title': title,
                    'description': description
                }
                
                async with session.post(finalize_url, data=finalize_data) as response:
                    if response.status != 200:
                        logger.error(f"Facebook upload finalize failed: {response.status}")
                        return None
                    
                    result = await response.json()
                    video_url = f"https://www.facebook.com/watch/?v={video_id}"
                    
                    logger.info(f"✓ Facebook upload successful: {video_url}")
                    return video_url
                    
        except Exception as e:
            logger.error(f"✗ Facebook upload failed: {e}")
            return None
    
    async def upload_to_instagram(self, video_path: str, meal_plan: Dict) -> Optional[str]:
        """
        Upload video to Instagram
        """
        try:
            instagram_creds = self.credentials.get('instagram', {})
            access_token = instagram_creds.get('access_token')
            user_id = instagram_creds.get('user_id')
            
            if not access_token or not user_id:
                logger.error("Instagram credentials not found")
                return None
            
            # Generate caption
            caption = self.generate_description(meal_plan, 'instagram_feed')
            
            async with aiohttp.ClientSession() as session:
                # Step 1: Create media container
                container_url = f"https://graph.facebook.com/v18.0/{user_id}/media"
                container_data = {
                    'access_token': access_token,
                    'video_url': video_path,  # This needs to be a public URL
                    'media_type': 'REELS',
                    'caption': caption
                }
                
                async with session.post(container_url, data=container_data) as response:
                    if response.status != 200:
                        logger.error(f"Instagram container creation failed: {response.status}")
                        return None
                    
                    container_result = await response.json()
                    container_id = container_result.get('id')
                
                # Step 2: Publish media
                publish_url = f"https://graph.facebook.com/v18.0/{user_id}/media_publish"
                publish_data = {
                    'access_token': access_token,
                    'creation_id': container_id
                }
                
                async with session.post(publish_url, data=publish_data) as response:
                    if response.status != 200:
                        logger.error(f"Instagram publish failed: {response.status}")
                        return None
                    
                    result = await response.json()
                    media_id = result.get('id')
                    
                    logger.info(f"✓ Instagram upload successful: {media_id}")
                    return f"https://www.instagram.com/p/{media_id}"
                    
        except Exception as e:
            logger.error(f"✗ Instagram upload failed: {e}")
            return None
    
    async def upload_to_tiktok(self, video_path: str, meal_plan: Dict) -> Optional[str]:
        """
        Upload video to TikTok
        """
        try:
            tiktok_creds = self.credentials.get('tiktok', {})
            access_token = tiktok_creds.get('access_token')
            
            if not access_token:
                logger.error("TikTok credentials not found")
                return None
            
            # Generate title and description
            title = self.generate_title(meal_plan, 'tiktok')
            
            async with aiohttp.ClientSession() as session:
                # TikTok API upload
                upload_url = "https://open-api.tiktok.com/share/video/upload/"
                
                with open(video_path, 'rb') as video_file:
                    upload_data = aiohttp.FormData()
                    upload_data.add_field('access_token', access_token)
                    upload_data.add_field('video', video_file, 
                                        filename=os.path.basename(video_path))
                    upload_data.add_field('text', title)
                    upload_data.add_field('privacy_level', 'PUBLIC_TO_EVERYONE')
                    
                    async with session.post(upload_url, data=upload_data) as response:
                        if response.status != 200:
                            logger.error(f"TikTok upload failed: {response.status}")
                            return None
                        
                        result = await response.json()
                        
                        if result.get('data', {}).get('error_code') == 0:
                            share_id = result.get('data', {}).get('share_id')
                            logger.info(f"✓ TikTok upload successful: {share_id}")
                            return f"https://www.tiktok.com/@username/video/{share_id}"
                        else:
                            logger.error(f"TikTok upload error: {result}")
                            return None
                            
        except Exception as e:
            logger.error(f"✗ TikTok upload failed: {e}")
            return None
    
    def generate_title(self, meal_plan: Dict, platform: str) -> str:
        """
        Generate platform-specific title
        """
        meals = meal_plan.get('meals', {})
        totals = meal_plan.get('totals', {})
        
        base_title = f"AI Meal Plan: {len(meals)} Meals, {totals.get('calories', 0)} Calories"
        
        settings = self.platform_settings.get(platform, {})
        suffix = settings.get('title_suffix', '')
        
        return base_title + suffix
    
    def generate_description(self, meal_plan: Dict, platform: str) -> str:
        """
        Generate platform-specific description
        """
        meals = meal_plan.get('meals', {})
        totals = meal_plan.get('totals', {})
        
        description = f"🤖 AI-Generated Meal Plan\\n\\n"
        description += f"📊 {len(meals)} carefully crafted meals\\n"
        description += f"🔥 {totals.get('calories', 0)} total calories\\n"
        description += f"💪 {totals.get('protein', 0)}g protein\\n"
        description += f"🍞 {totals.get('carbs', 0)}g carbs\\n"
        description += f"🥑 {totals.get('fat', 0)}g fat\\n\\n"
        
        description += "✨ Features:\\n"
        description += "• Personalized nutrition\\n"
        description += "• AI-optimized macros\\n"
        description += "• Balanced meal timing\\n"
        description += "• Easy-to-follow recipes\\n\\n"
        
        description += "🎯 Perfect for fitness enthusiasts, busy professionals, and anyone looking to improve their nutrition!\\n\\n"
        
        settings = self.platform_settings.get(platform, {})
        suffix = settings.get('description_suffix', '')
        
        return description + suffix
    
    async def upload_to_all_platforms(self, video_paths: Dict[str, str], meal_plan: Dict) -> Dict[str, str]:
        """
        Upload videos to all configured platforms
        """
        results = {}
        
        for platform, video_path in video_paths.items():
            if not video_path or not os.path.exists(video_path):
                logger.warning(f"Video file not found for {platform}: {video_path}")
                results[platform] = None
                continue
            
            try:
                if platform in ['youtube_shorts', 'youtube_long']:
                    result = await self.upload_to_youtube(video_path, platform, meal_plan)
                elif platform == 'facebook':
                    result = await self.upload_to_facebook(video_path, meal_plan)
                elif platform in ['instagram_feed', 'instagram_story']:
                    result = await self.upload_to_instagram(video_path, meal_plan)
                elif platform == 'tiktok':
                    result = await self.upload_to_tiktok(video_path, meal_plan)
                else:
                    logger.warning(f"Unsupported platform: {platform}")
                    result = None
                
                results[platform] = result
                
            except Exception as e:
                logger.error(f"Upload failed for {platform}: {e}")
                results[platform] = None
        
        return results
    
    def create_credentials_template(self):
        """
        Create a template credentials file
        """
        template = {
            "youtube": {
                "note": "Get credentials from Google Cloud Console - YouTube Data API v3"
            },
            "facebook": {
                "page_access_token": "YOUR_PAGE_ACCESS_TOKEN",
                "page_id": "YOUR_PAGE_ID",
                "note": "Get from Facebook Developer Console"
            },
            "instagram": {
                "access_token": "YOUR_ACCESS_TOKEN",
                "user_id": "YOUR_USER_ID",
                "note": "Get from Instagram Basic Display API"
            },
            "tiktok": {
                "access_token": "YOUR_ACCESS_TOKEN",
                "note": "Get from TikTok for Developers"
            }
        }
        
        with open('social_credentials_template.json', 'w') as f:
            json.dump(template, f, indent=2)
        
        logger.info("Created social_credentials_template.json")
        logger.info("Fill in your API credentials and rename to social_credentials.json")

# Example usage
async def main():
    """
    Example usage of the social media uploader
    """
    uploader = SocialMediaUploader()
    
    # Create credentials template if needed
    if not os.path.exists('social_credentials.json'):
        uploader.create_credentials_template()
        print("Please fill in your API credentials in social_credentials.json")
        return
    
    # Sample video paths (from video generator)
    video_paths = {
        'youtube_shorts': 'videos/youtube_shorts_20250117_120000.mp4',
        'youtube_long': 'videos/youtube_long_20250117_120000.mp4',
        'facebook': 'videos/facebook_20250117_120000.mp4',
        'instagram_feed': 'videos/instagram_feed_20250117_120000.mp4',
        'tiktok': 'videos/tiktok_20250117_120000.mp4'
    }
    
    # Sample meal plan
    meal_plan = {
        'meals': {
            'breakfast': {'calories': 350, 'protein': 25, 'carbs': 30, 'fat': 12},
            'lunch': {'calories': 450, 'protein': 35, 'carbs': 20, 'fat': 25}
        },
        'totals': {'calories': 800, 'protein': 60, 'carbs': 50, 'fat': 37}
    }
    
    # Upload to all platforms
    results = await uploader.upload_to_all_platforms(video_paths, meal_plan)
    
    print("\\n=== Upload Results ===")
    for platform, url in results.items():
        status = "✓ SUCCESS" if url else "✗ FAILED"
        print(f"{platform}: {status}")
        if url:
            print(f"  -> {url}")

if __name__ == "__main__":
    asyncio.run(main())