"""
Routes for AI Nutritionist Chat functionality
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, NutritionChat, ChatMessage, User
from ai_nutritionist import ai_nutritionist
from datetime import datetime, timezone
import json
from logging_setup import get_logger

logger = get_logger(__name__)
chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


@chat_bp.route('/')
@login_required
def chat_home():
    """Main chat interface"""
    try:
        # Get user's recent chats
        recent_chats = NutritionChat.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(NutritionChat.updated_at.desc()).limit(10).all()
        
        return render_template('chat_interface.html', recent_chats=recent_chats)
        
    except Exception as e:
        logger.error(f"Error loading chat interface: {str(e)}")
        flash('Error loading chat interface', 'error')
        return redirect(url_for('dashboard'))


@chat_bp.route('/new', methods=['POST'])
@login_required
def new_chat():
    """Create a new chat conversation"""
    try:
        data = request.get_json()
        title = data.get('title', 'Nutrition Chat')
        
        # Create new chat
        chat = NutritionChat(
            user_id=current_user.id,
            title=title
        )
        db.session.add(chat)
        db.session.commit()
        
        logger.info(f"User {current_user.id} created new chat {chat.id}")
        
        return jsonify({
            'success': True,
            'chat_id': chat.id,
            'title': chat.title,
            'created_at': chat.created_at.isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating new chat: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create new chat'}), 500


@chat_bp.route('/<int:chat_id>')
@login_required
def view_chat(chat_id):
    """View a specific chat conversation"""
    try:
        chat = NutritionChat.query.filter_by(
            id=chat_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not chat:
            flash('Chat not found', 'error')
            return redirect(url_for('chat.chat_home'))
        
        # Get all messages for this chat
        messages = chat.messages.order_by(ChatMessage.created_at.asc()).all()
        
        return render_template('chat_conversation.html',
                             chat=chat,
                             messages=messages)
        
    except Exception as e:
        logger.error(f"Error viewing chat {chat_id}: {str(e)}")
        flash('Error loading chat conversation', 'error')
        return redirect(url_for('chat.chat_home'))


@chat_bp.route('/<int:chat_id>/message', methods=['POST'])
@login_required
def send_message(chat_id):
    """Send a message and get AI response"""
    try:
        # Verify chat ownership
        chat = NutritionChat.query.filter_by(
            id=chat_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Check user credits/subscription
        if not _check_chat_permissions(current_user):
            return jsonify({'error': 'Insufficient credits or subscription required'}), 403
        
        # Add user message to chat
        user_msg = chat.add_message(user_message, 'user')
        
        # Get user context for personalized responses
        user_context = _get_user_context(current_user)
        
        # Get recent messages for context
        recent_messages = [msg.to_dict() for msg in chat.get_recent_messages(5)]
        
        # Generate AI response
        ai_response = ai_nutritionist.get_ai_response(
            user_message=user_message,
            user_context=user_context,
            chat_history=recent_messages
        )
        
        # Add AI response to chat
        ai_msg = chat.add_message(
            content=ai_response['content'],
            message_type='ai',
            ai_model=ai_response['model']
        )
        ai_msg.tokens_used = int(ai_response.get('tokens_used', 0))
        ai_msg.response_time_ms = ai_response.get('response_time_ms', 0)
        ai_msg.confidence_score = ai_response.get('confidence_score', 0.0)
        
        db.session.commit()
        
        # Log usage (deduct credits for free users)
        _log_chat_usage(current_user, ai_response.get('tokens_used', 0))
        
        logger.info(f"User {current_user.id} sent message in chat {chat_id}")
        
        return jsonify({
            'success': True,
            'user_message': user_msg.to_dict(),
            'ai_response': ai_msg.to_dict(),
            'remaining_credits': _get_remaining_credits(current_user)
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending message to chat {chat_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to send message'}), 500


@chat_bp.route('/<int:chat_id>/delete', methods=['POST'])
@login_required
def delete_chat(chat_id):
    """Delete a chat conversation"""
    try:
        chat = NutritionChat.query.filter_by(
            id=chat_id,
            user_id=current_user.id
        ).first()
        
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        # Soft delete - mark as inactive
        chat.is_active = False
        db.session.commit()
        
        logger.info(f"User {current_user.id} deleted chat {chat_id}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete chat'}), 500


@chat_bp.route('/api/messages/<int:chat_id>')
@login_required
def get_messages_api(chat_id):
    """API endpoint to get chat messages"""
    try:
        chat = NutritionChat.query.filter_by(
            id=chat_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404
        
        messages = chat.messages.order_by(ChatMessage.created_at.asc()).all()
        
        return jsonify({
            'chat_id': chat.id,
            'title': chat.title,
            'messages': [msg.to_dict() for msg in messages]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting messages for chat {chat_id}: {str(e)}")
        return jsonify({'error': 'Failed to get messages'}), 500


def _check_chat_permissions(user):
    """Check if user has permission to use chat (credits or subscription)"""
    if user.subscription_tier in ['pro', 'premium']:
        return True
    
    # Free users need credits
    return user.credits_balance > 0


def _get_user_context(user):
    """Get user context for personalized AI responses"""
    # This could be expanded to include user preferences from profile
    return {
        'subscription_tier': user.subscription_tier,
        'diet_type': 'balanced',  # Could come from user profile
        'calorie_target': 2000,   # Could come from user profile
        'goals': 'general health', # Could come from user profile
        'allergies': 'none'       # Could come from user profile
    }


def _log_chat_usage(user, tokens_used):
    """Log chat usage and deduct credits for free users"""
    try:
        # Deduct credits for free users (1 credit per chat interaction)
        if user.subscription_tier == 'free' and user.credits_balance > 0:
            user.credits_balance -= 1
            db.session.commit()
            
        # Could also log to UsageLog table for analytics
        
    except Exception as e:
        logger.error(f"Error logging chat usage for user {user.id}: {str(e)}")


def _get_remaining_credits(user):
    """Get remaining credits for user"""
    if user.subscription_tier in ['pro', 'premium']:
        return 'unlimited'
    return user.credits_balance