"""Email service for user engagement and retention."""

import os
from typing import Optional, Dict, Any
from flask import current_app, render_template_string
from flask_mail import Message
from app.extensions import mail

class EmailService:
    """Handle all email communications for user retention."""
    
    def __init__(self):
        self._enabled = None  # Lazy initialization
    
    def _check_email_config(self) -> bool:
        """Check if email is properly configured."""
        if not current_app:
            return False
        required_settings = ['MAIL_SERVER', 'MAIL_USERNAME', 'MAIL_PASSWORD']
        return all(current_app.config.get(setting) for setting in required_settings)
    
    @property
    def enabled(self) -> bool:
        """Lazy check for email configuration."""
        if self._enabled is None:
            self._enabled = self._check_email_config()
        return self._enabled
    
    def send_email(self, to: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """Send an email with error handling."""
        if not self.enabled:
            current_app.logger.warning("Email not configured - email not sent")
            return False
        
        try:
            msg = Message(
                subject=subject,
                recipients=[to],
                html=html_body,
                body=text_body or self._html_to_text(html_body),
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            mail.send(msg)
            current_app.logger.info(f"Email sent successfully to {to}: {subject}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {to}: {str(e)}")
            return False
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new user."""
        subject = "🎉 Welcome to Cibozer - Your AI Meal Planning Journey Starts Now!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .cta-button {{ background: #2ECC71; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .tips {{ background: #f8f9fa; padding: 20px; border-left: 4px solid #2ECC71; margin: 20px 0; }}
                .footer {{ background: #f1f1f1; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🍽️ Welcome to Cibozer!</h1>
                <p>Your personalized meal planning adventure begins now</p>
            </div>
            
            <div class="content">
                <h2>Hi {user_name}! 👋</h2>
                
                <p>We're thrilled you've joined the Cibozer community! You've just unlocked the power of AI-driven meal planning that will transform how you approach healthy eating.</p>
                
                <p><strong>Here's what you can do right now:</strong></p>
                <ul>
                    <li>🎯 <strong>Create your first meal plan</strong> - Takes less than 2 minutes</li>
                    <li>📱 <strong>Generate plans for any diet</strong> - Keto, Vegan, High Protein, and more</li>
                    <li>🏪 <strong>Get realistic portions</strong> - Kitchen-friendly measurements you can actually use</li>
                    <li>📋 <strong>Export shopping lists</strong> - Never forget an ingredient again</li>
                </ul>
                
                <div style="text-align: center;">
                    <a href="http://localhost:5000/create" class="cta-button">
                        🚀 Create Your First Meal Plan
                    </a>
                </div>
                
                <div class="tips">
                    <h3>💡 Pro Tips for Success:</h3>
                    <ul>
                        <li><strong>Start small:</strong> Try a 3-day plan first to get familiar</li>
                        <li><strong>Be specific:</strong> Choose your exact calorie target for better results</li>
                        <li><strong>Experiment:</strong> Try different diet types to find what works for you</li>
                        <li><strong>Save favorites:</strong> Bookmark meal plans you love for easy access</li>
                    </ul>
                </div>
                
                <p>Questions? Just reply to this email - we read every message and love helping you succeed!</p>
                
                <p>Happy meal planning! 🎉</p>
                <p><strong>The Cibozer Team</strong></p>
            </div>
            
            <div class="footer">
                <p>You're receiving this because you signed up for Cibozer. We'll only send you helpful content about meal planning.</p>
                <p>Cibozer - AI-Powered Meal Planning • Built with ❤️ for healthier eating</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_body)
    
    def send_first_meal_plan_celebration(self, user_email: str, user_name: str, meal_plan_info: Dict[str, Any]) -> bool:
        """Send celebration email after first successful meal plan generation."""
        subject = "🎉 Amazing! You just created your first meal plan!"
        
        days = meal_plan_info.get('days', 1)
        calories = meal_plan_info.get('calories', 2000)
        diet_type = meal_plan_info.get('diet_type', 'standard').title()
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .celebration {{ background: #f8f9fa; padding: 25px; border-radius: 10px; text-align: center; margin: 20px 0; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat {{ text-align: center; }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #2ECC71; }}
                .cta-button {{ background: #2ECC71; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px; }}
                .footer {{ background: #f1f1f1; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 Congratulations, {user_name}!</h1>
                <p>You just generated your first AI-powered meal plan!</p>
            </div>
            
            <div class="content">
                <div class="celebration">
                    <h2>🏆 Your First Success!</h2>
                    <p>You've officially joined the thousands of people using AI to simplify their meal planning. This is just the beginning!</p>
                </div>
                
                <h3>📊 Your Meal Plan Stats:</h3>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-number">{days}</div>
                        <div>Days</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{calories}</div>
                        <div>Calories/Day</div>
                    </div>
                    <div class="stat">
                        <div class="stat-number">{diet_type}</div>
                        <div>Diet Type</div>
                    </div>
                </div>
                
                <h3>🚀 What's Next?</h3>
                <ul>
                    <li><strong>Try different diets:</strong> Experiment with Keto, Vegan, or High Protein plans</li>
                    <li><strong>Adjust your calories:</strong> Fine-tune based on your goals</li>
                    <li><strong>Generate longer plans:</strong> Try a full 7-day meal plan</li>
                    <li><strong>Save your favorites:</strong> Keep track of meal plans you love</li>
                </ul>
                
                <div style="text-align: center;">
                    <a href="http://localhost:5000/create" class="cta-button">
                        🎯 Create Another Meal Plan
                    </a>
                    <a href="http://localhost:5000/profile" class="cta-button">
                        📊 View Your Dashboard
                    </a>
                </div>
                
                <p><strong>Remember:</strong> Consistency is key! Users who create meal plans weekly are 3x more likely to reach their health goals.</p>
                
                <p>Keep up the amazing work! 💪</p>
                <p><strong>The Cibozer Team</strong></p>
            </div>
            
            <div class="footer">
                <p>Stay motivated and keep planning! We're here to support your healthy eating journey.</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_body)
    
    def send_weekly_reminder(self, user_email: str, user_name: str, stats: Dict[str, Any]) -> bool:
        """Send weekly engagement reminder."""
        subject = "🗓️ Time for your weekly meal plan!"
        
        plans_created = stats.get('total_plans', 0)
        last_login = stats.get('days_since_last_login', 0)
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .motivation {{ background: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0; }}
                .cta-button {{ background: #2ECC71; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
                .footer {{ background: #f1f1f1; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🗓️ Weekly Planning Time!</h1>
                <p>Your healthy eating routine awaits</p>
            </div>
            
            <div class="content">
                <h2>Hi {user_name}! 👋</h2>
                
                <p>It's been {last_login} days since your last visit, and we miss you! 💚</p>
                
                <div class="motivation">
                    <h3>🎯 Your Progress So Far:</h3>
                    <ul>
                        <li>✅ <strong>{plans_created} meal plans created</strong> - You're building healthy habits!</li>
                        <li>🎯 <strong>Weekly planning</strong> - The key to consistent success</li>
                        <li>💪 <strong>Stay consistent</strong> - You're on the right track!</li>
                    </ul>
                </div>
                
                <h3>💡 This Week's Tip:</h3>
                <p><strong>Meal prep Sunday:</strong> Generate a full 7-day plan and prep ingredients for the week. Users who meal prep are 4x more likely to stick to their nutrition goals!</p>
                
                <div style="text-align: center;">
                    <a href="http://localhost:5000/create" class="cta-button">
                        🚀 Plan This Week's Meals
                    </a>
                </div>
                
                <p>Remember: Small, consistent actions lead to big results. You've got this! 💪</p>
                
                <p>Happy planning!</p>
                <p><strong>The Cibozer Team</strong></p>
            </div>
            
            <div class="footer">
                <p>We believe in your success! Keep planning, keep growing.</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_body)
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text for email fallback."""
        # Simple HTML to text conversion
        import re
        text = re.sub('<[^<]+?>', '', html)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

# Global email service instance
email_service = EmailService()