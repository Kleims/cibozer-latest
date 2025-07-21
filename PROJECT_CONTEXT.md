# Cibozer Project Context
*Last Updated: 2025-07-21*

## Project Overview
Cibozer is an AI-powered meal planning and video generation platform built with Flask. It provides personalized meal plans, generates cooking videos, and offers comprehensive nutrition tracking.

## Tech Stack

### Backend
- **Framework**: Flask 2.3.3
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login with secure password hashing
- **Payment Processing**: Stripe integration
- **Testing**: pytest with coverage reporting
- **Server**: Gunicorn for production

### Frontend
- **Templating**: Jinja2 (server-side rendering)
- **JavaScript**: Vanilla JS for client interactions
- **CSS**: Custom stylesheets
- **No modern framework** (React/Vue/Angular)

### Key Libraries
- **Video Processing**: OpenCV, MoviePy, edge-tts
- **Image Processing**: Pillow
- **PDF Generation**: ReportLab
- **Data Visualization**: Matplotlib
- **API Integrations**: Google API (YouTube), Stripe
- **Email**: Flask-Mail
- **Forms**: Flask-WTF with CSRF protection

## Architecture

### Core Modules
1. **app.py** - Main Flask application and route definitions
2. **models.py** - Database models (User, MealPlan, Payment, etc.)
3. **auth.py** - Authentication and authorization logic
4. **payments.py** - Stripe payment processing
5. **meal_optimizer.py** - AI meal planning algorithms
6. **video_generator.py** - Video creation pipeline
7. **pdf_generator.py** - PDF export functionality

### Directory Structure
```
/
├── static/           # CSS, JS, images, generated content
├── templates/        # Jinja2 HTML templates
│   ├── auth/        # Login, register, profile
│   └── admin/       # Admin dashboard
├── instance/        # SQLite database
├── migrations/      # Alembic database migrations
├── logs/           # Application logs
├── tests/          # pytest test suite
└── scripts/        # Utility and deployment scripts
```

## Current Issues & TODOs

### Known Issues
1. Test coverage needs improvement (currently low)
2. Some tests may be failing due to recent changes
3. Video generation can be memory-intensive
4. Need better error handling in payment flows

### Technical Debt
1. Refactor large route handlers into service classes
2. Improve separation of concerns in video generation
3. Add more comprehensive logging
4. Implement caching for expensive operations

### Security Considerations
- CSRF protection enabled
- Password hashing implemented
- File upload validation needed
- API rate limiting recommended

## Testing Strategy

### Test Organization
- Unit tests for individual functions
- Integration tests for routes
- Payment system tests (with mocks)
- Database tests with test fixtures

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest test_auth.py

# Run by marker
pytest -m "not slow"
```

### Critical Test Areas
1. Authentication flows
2. Payment processing
3. Video generation pipeline
4. Database operations
5. API endpoints

## Development Workflow

### Local Setup
1. Create virtual environment
2. Install requirements: `pip install -r requirements.txt`
3. Initialize database: `flask db upgrade`
4. Run development server: `python app.py`

### Database Management
- Migrations: `flask db migrate -m "message"`
- Upgrade: `flask db upgrade`
- Downgrade: `flask db downgrade`

### Environment Variables
Key variables needed:
- `SECRET_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `DATABASE_URL` (defaults to SQLite)
- `MAIL_USERNAME` / `MAIL_PASSWORD`

## Deployment

### Supported Platforms
- Render (render.yaml)
- Railway (railway.json)
- Vercel (vercel.json)
- Generic VPS with Gunicorn

### Production Considerations
- Use PostgreSQL instead of SQLite
- Configure proper logging
- Set up SSL/TLS
- Enable CDN for static assets
- Configure backup strategy

## Performance Optimization

### Current Bottlenecks
1. Video generation is CPU/memory intensive
2. Large meal plan calculations
3. PDF generation for complex reports

### Optimization Strategies
- Implement task queue (Celery/RQ)
- Add Redis caching
- Optimize database queries
- Lazy load heavy components

## Future Enhancements

### Planned Features
1. Mobile app API
2. Social features (sharing, following)
3. Advanced nutrition analytics
4. Recipe recommendations
5. Shopping list generation

### Architecture Improvements
1. Microservices for video processing
2. GraphQL API
3. Real-time updates with WebSockets
4. Machine learning pipeline

## Maintenance Notes

### Regular Tasks
- Monitor error logs
- Update dependencies
- Review security advisories
- Optimize database
- Clean up generated files

### Health Metrics
- Test suite pass rate
- Code coverage percentage
- Response time averages
- Memory usage patterns
- Error rate tracking

---

This document should be updated as the project evolves. Use it as a reference for understanding the codebase and making architectural decisions.