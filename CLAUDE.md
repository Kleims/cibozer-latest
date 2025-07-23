# Cibozer - AI Meal Planning Application

## Project Overview
Cibozer is a production Flask application for AI-powered meal planning with premium features.

## Key Components
- **Flask Backend**: Main app with blueprints (auth, main, payment, admin, share, api)
- **Models**: User, SavedMealPlan, Payment, UsageLog, SharedMealPlan
- **Services**: meal_optimizer.py (core AI), pdf_generator.py, video_generator.py
- **Frontend**: Bootstrap 5, responsive design, clean UI

## Critical Information
- User's livelihood depends on this app - quality is paramount
- Focus on real implementations, no stubs or placeholders
- All changes must be tested
- Premium features: PDF export, video generation, unlimited plans
- Free tier: 5 meal plans with registration

## Testing
- Run: `python -m pytest tests/`
- Key test files: test_app.py, test_models.py, test_meal_optimizer.py
- Aim for 90%+ test coverage

## Common Issues
- URL routing: Use blueprint prefixes (e.g., `url_for('main.index')`)
- Payments: Stripe integration (check if configured)
- Rate limiting: Applied to API endpoints
- Security headers: Must be present for all responses

## Development Priorities
1. Keep tests passing
2. Fix errors before adding features
3. Clean up technical debt regularly
4. Document significant changes