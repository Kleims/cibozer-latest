# 🍽️ Cibozer - AI-Powered Meal Planning

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-90%25+-brightgreen.svg)](./tests)
[![Security](https://img.shields.io/badge/security-A+-green.svg)](./SECURITY.md)

[Live Demo](https://cibozer.com) | [Documentation](./docs) | [API Reference](./API_DOCUMENTATION.md) | [Deployment Guide](./DEPLOYMENT_GUIDE.md)

## 🌟 Overview

Cibozer is a production-ready AI-powered meal planning SaaS platform that generates personalized meal plans, creates video content for social media, and helps users achieve their nutrition goals. Built with Flask and featuring advanced meal optimization algorithms, enterprise-grade security, and seamless payment integration.

### ✨ Key Features

#### Core Features
- 🤖 **AI Meal Planning**: Intelligent meal generation based on dietary preferences and calorie targets
- 🎯 **Personalized Nutrition**: Customized plans based on individual health goals
- 🛒 **Smart Shopping Lists**: Automated grocery lists grouped by category
- 📊 **Nutritional Analytics**: Detailed macro and micronutrient tracking
- 🔐 **Enterprise Security**: CSRF protection, rate limiting, secure authentication

#### Premium Features
- 🎥 **Video Generation**: Automated video creation for YouTube Shorts, TikTok, and Instagram
- 📄 **PDF Export**: Professional meal plans and grocery lists in PDF format
- 🔄 **Unlimited Plans**: Generate as many meal plans as needed
- 📧 **Email Integration**: Automatic delivery of meal plans
- 💳 **Subscription Tiers**: Stripe-powered billing for Pro ($9.99/mo) and Premium ($19.99/mo) tiers
- 📈 **Admin Dashboard**: Comprehensive analytics and user management interface

## Quick Start

### Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cibozer.git
cd cibozer
```

2. Create and activate virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.template .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

6. Run the application:
```bash
python app.py
```

Visit http://localhost:5001 to access the application.

## Configuration

### Required Environment Variables

```env
# Security
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///cibozer.db  # or PostgreSQL URL for production

# Stripe (Optional - for payments)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PRO=price_...
STRIPE_PRICE_ID_PREMIUM=price_...

# Admin (Optional)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure-password
```

### Optional Features

**Video Uploads**: To enable social media uploads:

1. Copy the credentials template:
```bash
cp social_credentials_template.json social_credentials.json
```

2. Configure API credentials for each platform:

   **YouTube**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Enable YouTube Data API v3
   - Create credentials (OAuth 2.0 Client ID)
   - Download and save credentials

   **Facebook/Instagram**:
   - Visit [Facebook Developers](https://developers.facebook.com)
   - Create an app and get Page Access Token
   - For Instagram, enable Instagram Basic Display API

   **TikTok**:
   - Register at [TikTok for Developers](https://developers.tiktok.com)
   - Create an app and get access token

3. Update `social_credentials.json` with your credentials

4. Restart the application

## Project Structure

```
cibozer/
├── app.py              # Main Flask application
├── models.py           # Database models
├── auth.py             # Authentication routes
├── admin.py            # Admin panel routes
├── payments.py         # Payment processing
├── share_routes.py     # Sharing functionality
├── meal_optimizer.py   # Core meal planning algorithm
├── video_service.py    # Video generation service
├── pdf_generator.py    # PDF export functionality
├── app_config.py       # Centralized configuration
├── logging_setup.py    # Logging configuration
├── middleware.py       # Request validation middleware
├── requirements.txt    # Python dependencies
├── .env.template       # Environment variables template
├── core/               # Core application modules (future)
├── routes/             # Route blueprints (future)
├── services/           # Service layer modules (future)
├── scripts/            # Utility and setup scripts
├── tests/              # Test suite
├── docs/               # Documentation
│   ├── api.md          # API documentation
│   ├── plans/          # Project plans
│   ├── audits/         # Audit reports
│   └── technical/      # Technical documentation
├── templates/          # HTML templates
├── static/             # CSS, JS, images
└── migrations/         # Database migrations
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout

### Meal Planning
- `POST /api/generate-meal-plan` - Generate AI meal plan
- `GET /api/save-meal-plan` - Save meal plan
- `GET /api/meal-plans` - List saved meal plans

### Video Generation
- `POST /api/generate-video` - Create video from meal plan
- `GET /api/video/platforms` - Get supported platforms
- `GET /api/video/stats` - Video generation statistics

### User Management
- `GET /api/user/profile` - Get user profile
- `POST /api/user/upgrade` - Upgrade subscription
- `GET /api/credits` - Check credit balance

## Testing

Run the test suite:
```bash
pytest -v
```

Run with coverage:
```bash
pytest --cov=. --cov-report=html
```

## Deployment

The application supports multiple deployment platforms:

### Vercel
```bash
vercel --prod
```

### Heroku
```bash
git push heroku main
```

### Railway
```bash
railway up
```

### Docker
```bash
docker build -t cibozer .
docker run -p 5001:5001 cibozer
```

See platform-specific configuration files:
- `vercel.json` - Vercel configuration
- `Procfile` - Heroku configuration
- `railway.json` - Railway configuration
- `render.yaml` - Render configuration

## Architecture

```
cibozer/
├── app.py              # Main Flask application
├── models.py           # Database models
├── auth.py             # Authentication routes
├── admin.py            # Admin dashboard
├── payments.py         # Stripe integration
├── meal_optimizer.py   # AI meal planning engine
├── video_service.py    # Video generation service
├── pdf_generator.py    # PDF export functionality
├── templates/          # HTML templates
├── static/             # CSS, JS, images
└── tests/              # Test suite
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Ensure all tests pass before submitting PR

## Security

- CSRF protection on all forms
- Bcrypt password hashing
- Rate limiting (10 requests/minute)
- Security headers (CSP, X-Frame-Options)
- Input validation and sanitization

Report security vulnerabilities to: security@cibozer.com

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Documentation: [docs.cibozer.com](https://docs.cibozer.com)
- Issues: [GitHub Issues](https://github.com/yourusername/cibozer/issues)
- Email: support@cibozer.com

## Acknowledgments

- Flask community for the excellent framework
- OpenCV for video processing capabilities
- Edge TTS for voice synthesis
- All contributors and beta testers

---

Built with ❤️ by the Cibozer Team