# Cibozer Production Deployment Guide

## 🚀 Critical Security Fixes Applied

### ✅ Security Issues Resolved
- **Removed hardcoded production secrets** from `.env`
- **Added production WSGI server** (Gunicorn)
- **Fixed credit bypass vulnerability** in meal plan generation
- **Enhanced health monitoring** and error handling

## 🛠️ Production Setup

### 1. Environment Variables
Create a secure `.env` file with:

```bash
# REQUIRED: Generate secure values
SECRET_KEY=your-super-secret-key-here-64-chars-minimum
DATABASE_URL=postgresql://user:pass@host:port/dbname
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password

# Optional: Stripe integration
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key

# Production settings
FLASK_ENV=production
DEBUG=False
```

### 2. Generate Secure Secret Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Production Server Options

#### Option A: Railway
```bash
# Deploy with Railway (recommended)
railway login
railway init
railway up
```

#### Option B: Heroku
```bash
# Uses Procfile automatically
git push heroku main
```

#### Option C: VPS/Docker
```bash
# Install dependencies
pip install -r requirements.txt

# Run production server
chmod +x start_production.sh
./start_production.sh
```

## 📊 Monitoring Endpoints

- **Health Check**: `GET /api/health`
- **Metrics**: `GET /api/metrics`
- **User Status**: `GET /api/user-status` (authenticated)

## 🔒 Security Features

### Authentication
- Flask-Login with session management
- Password hashing with bcrypt
- CSRF protection enabled

### Rate Limiting
- 3 requests per minute per IP
- Credit-based usage limiting
- Premium tier bypass

### Security Headers
- Content Security Policy
- XSS Protection
- Frame Options
- HSTS enabled

## 💰 Business Model

### Credit System
- **Free**: 3 meal plans
- **Pro**: $9.99/month - Unlimited plans
- **Premium**: $19.99/month - All features

### Revenue Protection
- Credit enforcement restored
- Usage tracking implemented
- Subscription validation

## 🚨 Critical Next Steps

1. **Generate new SECRET_KEY** for production
2. **Set up PostgreSQL database** (not SQLite)
3. **Configure Stripe webhook endpoints**
4. **Set up SSL certificate**
5. **Monitor health endpoints**

## 🧪 Testing

### Local Testing
```bash
# Test production setup locally
python wsgi.py
```

### Health Checks
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/metrics
```

## 📈 Performance Optimizations Applied

- **Gunicorn workers**: 4 processes
- **Request timeout**: 120 seconds
- **Max requests per worker**: 1000
- **Database session management**
- **Static file optimization**

---

**⚠️ IMPORTANT**: This fixes critical production vulnerabilities. Deploy immediately with secure environment variables.