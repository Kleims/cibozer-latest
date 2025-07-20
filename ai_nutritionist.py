"""
AI Nutritionist Chat Service
Provides intelligent nutrition advice using OpenAI-style API
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from logging_setup import get_logger

logger = get_logger(__name__)

class AINutritionistService:
    """AI-powered nutrition assistant service"""
    
    def __init__(self):
        self.model_name = "nutrition-gpt-3.5"
        self.max_tokens = 500
        self.temperature = 0.7
        
    def get_ai_response(self, user_message: str, user_context: Optional[Dict] = None, 
                       chat_history: Optional[List[Dict]] = None) -> Dict:
        """
        Generate AI nutritionist response
        
        Args:
            user_message: The user's question or message
            user_context: User's dietary preferences, goals, etc.
            chat_history: Previous messages for context
            
        Returns:
            Dict with AI response and metadata
        """
        start_time = time.time()
        
        try:
            # Build context for AI
            system_prompt = self._build_system_prompt(user_context)
            conversation = self._build_conversation(system_prompt, user_message, chat_history)
            
            # Simulate AI response (in production, this would call OpenAI API)
            ai_response = self._generate_mock_response(user_message, user_context)
            
            response_time = int((time.time() - start_time) * 1000)
            
            result = {
                'content': ai_response,
                'model': self.model_name,
                'response_time_ms': response_time,
                'tokens_used': len(ai_response.split()) * 1.3,  # Rough estimate
                'confidence_score': 0.85,
                'success': True
            }
            
            logger.info(f"AI response generated in {response_time}ms")
            return result
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return {
                'content': "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
                'model': self.model_name,
                'response_time_ms': int((time.time() - start_time) * 1000),
                'tokens_used': 0,
                'confidence_score': 0.0,
                'success': False,
                'error': str(e)
            }
    
    def _build_system_prompt(self, user_context: Optional[Dict] = None) -> str:
        """Build system prompt for AI nutritionist"""
        base_prompt = """You are a helpful AI nutritionist assistant for Cibozer, an AI-powered meal planning platform. 
        
Your role is to:
- Provide evidence-based nutrition advice
- Help users with meal planning questions
- Suggest healthy recipes and food combinations
- Explain nutritional concepts in simple terms
- Consider dietary restrictions and preferences
- Encourage healthy eating habits

Guidelines:
- Always be supportive and encouraging
- Provide practical, actionable advice
- Cite general nutritional principles when helpful
- Never diagnose medical conditions
- Recommend consulting healthcare providers for serious health concerns
- Keep responses concise but informative
"""
        
        if user_context:
            context_addition = f"""
            
User Context:
- Dietary preferences: {user_context.get('diet_type', 'Not specified')}
- Calorie target: {user_context.get('calorie_target', 'Not specified')}
- Health goals: {user_context.get('goals', 'Not specified')}
- Allergies/restrictions: {user_context.get('allergies', 'None specified')}
"""
            base_prompt += context_addition
            
        return base_prompt
    
    def _build_conversation(self, system_prompt: str, user_message: str, 
                          chat_history: Optional[List[Dict]] = None) -> List[Dict]:
        """Build conversation array for AI API"""
        conversation = [{"role": "system", "content": system_prompt}]
        
        # Add recent chat history for context
        if chat_history:
            for msg in chat_history[-5:]:  # Last 5 messages
                role = "assistant" if msg['message_type'] == 'ai' else "user"
                conversation.append({"role": role, "content": msg['content']})
        
        # Add current user message
        conversation.append({"role": "user", "content": user_message})
        
        return conversation
    
    def _generate_mock_response(self, user_message: str, user_context: Optional[Dict] = None) -> str:
        """
        Generate mock AI responses for development/testing
        In production, this would be replaced with actual OpenAI API calls
        """
        message_lower = user_message.lower()
        
        # Meal planning questions
        if any(word in message_lower for word in ['meal plan', 'meal planning', 'what should i eat']):
            return self._meal_planning_response(user_context)
        
        # Weight loss questions
        elif any(word in message_lower for word in ['lose weight', 'weight loss', 'diet']):
            return self._weight_loss_response(user_context)
        
        # Nutrition questions
        elif any(word in message_lower for word in ['protein', 'carbs', 'calories', 'nutrition']):
            return self._nutrition_response(user_message, user_context)
        
        # Recipe questions
        elif any(word in message_lower for word in ['recipe', 'cook', 'prepare']):
            return self._recipe_response(user_message, user_context)
        
        # Healthy food questions
        elif any(word in message_lower for word in ['healthy', 'good for', 'benefits']):
            return self._healthy_food_response(user_message)
        
        # Default response
        else:
            return self._general_response(user_message, user_context)
    
    def _meal_planning_response(self, user_context: Optional[Dict] = None) -> str:
        """Generate meal planning advice"""
        responses = [
            "Great question! For effective meal planning, I recommend starting with your protein source for each meal, then adding complex carbs and plenty of vegetables. Would you like me to suggest a specific meal plan based on your goals?",
            
            "Meal planning is one of the best habits for healthy eating! Consider preparing proteins in bulk, keeping versatile ingredients on hand, and planning for 3-4 days at a time to maintain freshness.",
            
            "For successful meal planning, focus on balance: aim for lean proteins, whole grains, healthy fats, and colorful vegetables in each meal. What specific dietary preferences or goals do you have?"
        ]
        
        if user_context and user_context.get('calorie_target'):
            calorie_target = user_context['calorie_target']
            return f"Based on your {calorie_target} calorie target, I'd recommend dividing your meals into roughly 25% breakfast, 35% lunch, 35% dinner, and 5% snacks. Focus on nutrient-dense foods to meet your goals efficiently."
        
        import random
        return random.choice(responses)
    
    def _weight_loss_response(self, user_context: Optional[Dict] = None) -> str:
        """Generate weight loss advice"""
        return """For healthy weight loss, focus on creating a moderate calorie deficit through both diet and exercise. Key strategies include:

• Prioritize protein (0.8-1g per lb body weight) to maintain muscle
• Fill half your plate with non-starchy vegetables
• Choose complex carbs over simple sugars
• Stay hydrated and get adequate sleep
• Aim for 1-2 lbs loss per week for sustainability

Remember, sustainable changes are more important than quick fixes. Would you like help creating a specific meal plan?"""
    
    def _nutrition_response(self, user_message: str, user_context: Optional[Dict] = None) -> str:
        """Generate nutrition-focused responses"""
        if 'protein' in user_message.lower():
            return "Protein is essential for muscle maintenance, satiety, and metabolic health. Good sources include lean meats, fish, eggs, legumes, Greek yogurt, and quinoa. Aim for 20-30g per meal for optimal muscle protein synthesis."
        
        elif 'carbs' in user_message.lower() or 'carbohydrates' in user_message.lower():
            return "Carbohydrates are your body's preferred energy source! Focus on complex carbs like oats, quinoa, sweet potatoes, and brown rice. These provide steady energy and important nutrients, unlike simple sugars that cause energy spikes."
        
        elif 'calories' in user_message.lower():
            return "Calories are units of energy from food. For weight maintenance, balance calories in vs. calories out. For weight loss, create a moderate deficit. Quality matters too - 100 calories of nuts provides different nutrition than 100 calories of candy!"
        
        else:
            return "Nutrition is about nourishing your body with the right balance of macronutrients (protein, carbs, fats) and micronutrients (vitamins, minerals). Focus on whole foods, variety, and consistency for best results!"
    
    def _recipe_response(self, user_message: str, user_context: Optional[Dict] = None) -> str:
        """Generate recipe suggestions"""
        return """Here's a simple, nutritious recipe idea:

**Quick Protein Bowl:**
• Base: Brown rice or quinoa
• Protein: Grilled chicken, tofu, or beans
• Veggies: Roasted broccoli, bell peppers, spinach
• Healthy fat: Avocado or nuts
• Flavor: Lemon-herb dressing or tahini sauce

This combination provides complete nutrition and can be customized based on your preferences. Would you like more specific recipes for your dietary needs?"""
    
    def _healthy_food_response(self, user_message: str) -> str:
        """Generate responses about healthy foods"""
        return "Whole, minimally processed foods are generally the healthiest choices! Focus on colorful vegetables, lean proteins, whole grains, healthy fats (like avocados and nuts), and fruits. These foods provide essential nutrients while supporting your energy levels and overall health."
    
    def _general_response(self, user_message: str, user_context: Optional[Dict] = None) -> str:
        """Generate general helpful responses"""
        return f"Thank you for your question! I'm here to help with nutrition and meal planning advice. Could you tell me more specifically what you'd like to know about? I can help with meal planning, nutrition education, healthy recipes, or dietary guidance."

# Singleton instance
ai_nutritionist = AINutritionistService()