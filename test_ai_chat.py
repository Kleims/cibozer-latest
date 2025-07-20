"""
Tests for AI Nutritionist Chat functionality
"""

import pytest
from app import app, db
from models import User, NutritionChat, ChatMessage
from ai_nutritionist import AINutritionistService
from datetime import datetime, timezone, timedelta
import json


@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def authenticated_user(client):
    """Create and authenticate a test user"""
    with app.app_context():
        # Create test user
        user = User(
            email='test@example.com',
            full_name='Test User',
            subscription_tier='pro',
            credits_balance=10
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        # Login
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        return user


@pytest.fixture
def free_user(client):
    """Create a free tier user"""
    with app.app_context():
        user = User(
            email='free@example.com',
            full_name='Free User',
            subscription_tier='free',
            credits_balance=3
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user


class TestNutritionChatModel:
    """Test the NutritionChat model"""
    
    def test_create_chat(self):
        """Test creating a nutrition chat"""
        with app.app_context():
            chat = NutritionChat(
                user_id=1,
                title='My Nutrition Chat'
            )
            
            assert chat.title == 'My Nutrition Chat'
            assert chat.is_active is True
            assert chat.user_id == 1
    
    def test_add_message(self):
        """Test adding messages to chat"""
        with app.app_context():
            chat = NutritionChat(user_id=1)
            db.session.add(chat)
            db.session.commit()
            
            # Add user message
            user_msg = chat.add_message('Hello', 'user')
            assert user_msg.content == 'Hello'
            assert user_msg.message_type == 'user'
            
            # Add AI message
            ai_msg = chat.add_message('Hi there!', 'ai', 'gpt-3.5')
            assert ai_msg.content == 'Hi there!'
            assert ai_msg.message_type == 'ai'
            assert ai_msg.ai_model == 'gpt-3.5'
    
    def test_get_recent_messages(self):
        """Test getting recent messages"""
        with app.app_context():
            chat = NutritionChat(user_id=1)
            db.session.add(chat)
            db.session.commit()
            
            # Add multiple messages
            for i in range(15):
                chat.add_message(f'Message {i}', 'user')
            
            db.session.commit()
            
            # Should return 10 most recent
            recent = chat.get_recent_messages(10)
            assert len(recent) == 10
            assert recent[0].content == 'Message 14'  # Most recent first


class TestChatMessage:
    """Test ChatMessage model"""
    
    def test_message_to_dict(self):
        """Test converting message to dictionary"""
        with app.app_context():
            message = ChatMessage(
                chat_id=1,
                content='Test message',
                message_type='user'
            )
            
            result = message.to_dict()
            assert result['content'] == 'Test message'
            assert result['message_type'] == 'user'
            assert 'created_at' in result


class TestAINutritionistService:
    """Test the AI Nutritionist Service"""
    
    def test_meal_planning_response(self):
        """Test meal planning responses"""
        service = AINutritionistService()
        
        response = service.get_ai_response("I need help with meal planning")
        
        assert response['success'] is True
        assert 'meal' in response['content'].lower()
        assert response['model'] == 'nutrition-gpt-3.5'
        assert response['tokens_used'] > 0
    
    def test_weight_loss_response(self):
        """Test weight loss advice"""
        service = AINutritionistService()
        
        response = service.get_ai_response("How do I lose weight?")
        
        assert response['success'] is True
        assert any(word in response['content'].lower() for word in ['deficit', 'protein', 'exercise'])
    
    def test_nutrition_response(self):
        """Test nutrition-specific questions"""
        service = AINutritionistService()
        
        response = service.get_ai_response("How much protein should I eat?")
        
        assert response['success'] is True
        assert 'protein' in response['content'].lower()
    
    def test_user_context_integration(self):
        """Test using user context in responses"""
        service = AINutritionistService()
        
        user_context = {
            'calorie_target': 1800,
            'diet_type': 'vegetarian',
            'goals': 'weight loss'
        }
        
        response = service.get_ai_response(
            "What should I eat for dinner?",
            user_context=user_context
        )
        
        assert response['success'] is True
        assert len(response['content']) > 0
    
    def test_chat_history_context(self):
        """Test using chat history for context"""
        service = AINutritionistService()
        
        chat_history = [
            {'content': 'I am vegetarian', 'message_type': 'user'},
            {'content': 'Great! I can help with vegetarian meal planning.', 'message_type': 'ai'}
        ]
        
        response = service.get_ai_response(
            "What protein sources do you recommend?",
            chat_history=chat_history
        )
        
        assert response['success'] is True


class TestChatRoutes:
    """Test chat route endpoints"""
    
    def test_chat_home_authenticated(self, client, authenticated_user):
        """Test accessing chat home page"""
        response = client.get('/chat/')
        assert response.status_code == 200
    
    def test_chat_home_unauthenticated(self, client):
        """Test accessing chat without authentication"""
        response = client.get('/chat/')
        assert response.status_code == 302  # Redirect to login
    
    def test_create_new_chat(self, client, authenticated_user):
        """Test creating a new chat"""
        response = client.post('/chat/new',
                              json={'title': 'My Test Chat'},
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['title'] == 'My Test Chat'
        assert 'chat_id' in data
    
    def test_send_message(self, client, authenticated_user):
        """Test sending a message to chat"""
        with app.app_context():
            # Create a chat
            chat = NutritionChat(
                user_id=authenticated_user.id,
                title='Test Chat'
            )
            db.session.add(chat)
            db.session.commit()
            chat_id = chat.id
        
        # Send message
        response = client.post(f'/chat/{chat_id}/message',
                              json={'message': 'What should I eat for breakfast?'},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user_message' in data
        assert 'ai_response' in data
    
    def test_send_empty_message(self, client, authenticated_user):
        """Test sending empty message"""
        with app.app_context():
            chat = NutritionChat(user_id=authenticated_user.id)
            db.session.add(chat)
            db.session.commit()
            chat_id = chat.id
        
        response = client.post(f'/chat/{chat_id}/message',
                              json={'message': ''},
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Message cannot be empty' in data['error']
    
    def test_unauthorized_chat_access(self, client, authenticated_user):
        """Test accessing someone else's chat"""
        with app.app_context():
            # Create chat for different user
            chat = NutritionChat(user_id=999)  # Different user
            db.session.add(chat)
            db.session.commit()
            chat_id = chat.id
        
        response = client.post(f'/chat/{chat_id}/message',
                              json={'message': 'Hello'},
                              content_type='application/json')
        
        assert response.status_code == 404
    
    def test_free_user_credits(self, client, free_user):
        """Test free user credit deduction"""
        # Login as free user
        client.post('/auth/login', data={
            'email': 'free@example.com',
            'password': 'testpass123'
        })
        
        with app.app_context():
            chat = NutritionChat(user_id=free_user.id)
            db.session.add(chat)
            db.session.commit()
            chat_id = chat.id
            initial_credits = free_user.credits_balance
        
        # Send message
        response = client.post(f'/chat/{chat_id}/message',
                              json={'message': 'Help me plan meals'},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check credits were deducted
        with app.app_context():
            updated_user = User.query.get(free_user.id)
            assert updated_user.credits_balance == initial_credits - 1
    
    def test_delete_chat(self, client, authenticated_user):
        """Test deleting a chat"""
        with app.app_context():
            chat = NutritionChat(user_id=authenticated_user.id)
            db.session.add(chat)
            db.session.commit()
            chat_id = chat.id
        
        response = client.post(f'/chat/{chat_id}/delete')
        assert response.status_code == 200
        
        # Verify chat is marked inactive
        with app.app_context():
            deleted_chat = NutritionChat.query.get(chat_id)
            assert deleted_chat.is_active is False
    
    def test_get_messages_api(self, client, authenticated_user):
        """Test getting messages via API"""
        with app.app_context():
            chat = NutritionChat(user_id=authenticated_user.id)
            db.session.add(chat)
            db.session.commit()
            
            # Add some messages
            chat.add_message('Hello', 'user')
            chat.add_message('Hi there!', 'ai')
            db.session.commit()
            chat_id = chat.id
        
        response = client.get(f'/chat/api/messages/{chat_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['chat_id'] == chat_id
        assert len(data['messages']) == 2
        assert data['messages'][0]['content'] == 'Hello'
        assert data['messages'][1]['content'] == 'Hi there!'


class TestChatPermissions:
    """Test chat permission system"""
    
    def test_pro_user_unlimited_access(self, client):
        """Test pro users have unlimited access"""
        with app.app_context():
            pro_user = User(
                email='pro@example.com',
                subscription_tier='pro',
                credits_balance=0  # No credits but should still work
            )
            
            from chat_routes import _check_chat_permissions
            assert _check_chat_permissions(pro_user) is True
    
    def test_free_user_with_credits(self, client):
        """Test free user with credits"""
        with app.app_context():
            free_user = User(
                email='free@example.com',
                subscription_tier='free',
                credits_balance=5
            )
            
            from chat_routes import _check_chat_permissions
            assert _check_chat_permissions(free_user) is True
    
    def test_free_user_no_credits(self, client):
        """Test free user without credits"""
        with app.app_context():
            free_user = User(
                email='free@example.com',
                subscription_tier='free',
                credits_balance=0
            )
            
            from chat_routes import _check_chat_permissions
            assert _check_chat_permissions(free_user) is False


class TestErrorHandling:
    """Test error handling in chat system"""
    
    def test_invalid_chat_id(self, client, authenticated_user):
        """Test accessing non-existent chat"""
        response = client.get('/chat/99999')
        assert response.status_code == 302  # Redirect with flash message
    
    def test_malformed_json(self, client, authenticated_user):
        """Test sending malformed JSON"""
        with app.app_context():
            chat = NutritionChat(user_id=authenticated_user.id)
            db.session.add(chat)
            db.session.commit()
            chat_id = chat.id
        
        response = client.post(f'/chat/{chat_id}/message',
                              data='invalid json',
                              content_type='application/json')
        
        assert response.status_code == 400