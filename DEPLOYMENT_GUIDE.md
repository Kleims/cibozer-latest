# 🚀 Cibozer Production Deployment Guide

This guide provides step-by-step instructions for deploying Cibozer to production using various deployment platforms.

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have completed the following:

### ✅ 1. Environment Configuration
- [ ] Created `.env.production` file (copy from `.env.example`)
- [ ] Set all required environment variables
- [ ] Generated secure `SECRET_KEY`
- [ ] Configured email service (SendGrid recommended)
- [ ] Set up Stripe payment keys (production keys)
- [ ] Configured admin credentials

### ✅ 2. Database Preparation
- [ ] Set up PostgreSQL database
- [ ] Run database migrations
- [ ] Create admin user
- [ ] Test database connectivity

### ✅ 3. Testing & Validation
- [ ] Run production environment validation: `python scripts/validate_production_env.py`
- [ ] Run deployment preparation: `python scripts/prepare_production_deployment.py`
- [ ] Execute test suite: `python -m pytest`
- [ ] Verify all critical functionality works

---

## 🚂 Railway Deployment

Railway is the **recommended** deployment platform for Cibozer due to its simplicity and PostgreSQL/Redis integration.

### Step 1: Railway Setup
1. Create account at [railway.app](https://railway.app)
2. Install Railway CLI: `npm install -g @railway/cli`
3. Login: `railway login`

### Step 2: Create Project
```bash
# In your project directory
railway login
railway init
railway link
```

### Step 3: Configure Environment Variables
Set these variables in Railway dashboard or via CLI:

```bash
# Core Application
railway variables set SECRET_KEY="your-32-character-secret-key"
railway variables set FLASK_ENV="production"
railway variables set DEBUG="False"

# Email Configuration (SendGrid recommended)
railway variables set MAIL_SERVER="smtp.sendgrid.net"
railway variables set MAIL_PORT="587" 
railway variables set MAIL_USE_TLS="True"
railway variables set MAIL_USERNAME="apikey"
railway variables set MAIL_PASSWORD="your-sendgrid-api-key"
railway variables set MAIL_DEFAULT_SENDER="Cibozer <noreply@yourdomain.com>"

# Stripe Configuration
railway variables set STRIPE_SECRET_KEY="sk_live_your_live_key"
railway variables set STRIPE_PUBLISHABLE_KEY="pk_live_your_live_key"
railway variables set STRIPE_WEBHOOK_SECRET="whsec_your_webhook_secret"
railway variables set STRIPE_PRICE_ID_PRO="price_your_pro_price_id"
railway variables set STRIPE_PRICE_ID_PREMIUM="price_your_premium_price_id"

# Admin Configuration
railway variables set ADMIN_USERNAME="admin"
railway variables set ADMIN_EMAIL="admin@yourdomain.com"
railway variables set ADMIN_PASSWORD="secure-admin-password"
```

### Step 4: Add Database Services
```bash
# Add PostgreSQL
railway add postgresql

# Add Redis
railway add redis
```

### Step 5: Deploy
```bash
# Deploy to Railway
railway up

# Check deployment status
railway status

# View logs
railway logs
```

### Step 6: Post-Deployment
1. **Database Setup**: Railway will automatically run database migrations
2. **Custom Domain**: Configure custom domain in Railway dashboard
3. **SSL**: Automatic SSL certificates provided
4. **Monitoring**: Enable monitoring in Railway dashboard

---

## 🎨 Render Deployment

Render provides excellent PostgreSQL integration and automatic SSL certificates.

### Step 1: Render Setup
1. Create account at [render.com](https://render.com)
2. Connect your GitHub repository
3. Use the provided `render.yaml` configuration

### Step 2: Configure Blueprint
1. Go to Render Dashboard
2. Click "New" → "Blueprint"
3. Connect your repository
4. Render will automatically detect `render.yaml`

### Step 3: Environment Variables
Set these in Render dashboard (they're not in the YAML for security):

**Required Variables:**
- `SECRET_KEY`: Generate 32-character secret key
- `MAIL_PASSWORD`: Your SendGrid API key
- `STRIPE_SECRET_KEY`: Live Stripe secret key
- `STRIPE_PUBLISHABLE_KEY`: Live Stripe publishable key
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook secret
- `STRIPE_PRICE_ID_PRO`: Pro tier price ID
- `STRIPE_PRICE_ID_PREMIUM`: Premium tier price ID
- `ADMIN_PASSWORD`: Secure admin password
- `OPENAI_API_KEY`: (Optional) OpenAI API key

### Step 4: Deploy
1. Click "Apply" in Blueprint setup
2. Render will create all services automatically
3. Monitor deployment in dashboard

### Step 5: Post-Deployment
1. **Custom Domain**: Add custom domain in service settings
2. **SSL**: Automatic Let's Encrypt certificates
3. **Database Access**: Use provided connection strings

---

## 🐳 Docker Deployment

For self-hosted or cloud container deployments.

### Production Docker Compose
```bash
# Create production environment file
cp .env.example .env.production
# Edit .env.production with production values

# Build and start production services
docker-compose -f docker-compose.yml --profile production up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f web
```

### Docker Image Only
```bash
# Build production image
docker build -t cibozer:latest .

# Run with environment variables
docker run -d \
  --name cibozer \
  -p 5000:5000 \
  --env-file .env.production \
  cibozer:latest
```

---

## 🔧 Post-Deployment Configuration

### 1. Database Setup
After first deployment, initialize the database:

```bash
# Railway
railway run python scripts/init_production_database.py

# Render (via shell)
python scripts/init_production_database.py

# Docker
docker-compose exec web python scripts/init_production_database.py
```

### 2. Admin Access
- **URL**: `https://yourdomain.com/admin`
- **Username**: Value of `ADMIN_EMAIL` environment variable
- **Password**: Value of `ADMIN_PASSWORD` environment variable

### 3. Stripe Webhook Configuration
1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://yourdomain.com/webhooks/stripe`
3. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copy webhook secret to `STRIPE_WEBHOOK_SECRET` environment variable

### 4. Email Configuration Testing
Test email functionality:
```bash
# In production environment
python -c "
from app import create_app
from app.services.email_service import email_service
app = create_app('production')
with app.app_context():
    result = email_service.send_welcome_email('test@example.com', 'Test User')
    print('Email test result:', result)
"
```

### 5. Domain and SSL Configuration
- **Railway**: Configure custom domain in project settings
- **Render**: Add custom domain in service settings
- **Docker**: Configure reverse proxy (nginx) with SSL certificates

---

## 📊 Monitoring and Maintenance

### Health Checks
- **Endpoint**: `https://yourdomain.com/api/health`
- **Monitoring**: `https://yourdomain.com/admin/monitoring`

### Logs Access
```bash
# Railway
railway logs --tail

# Render
# View logs in dashboard

# Docker
docker-compose logs -f web
```

### Database Backups
```bash
# Railway
railway run python scripts/migrate_to_postgresql.py --backup-only

# Docker
docker-compose exec web python scripts/migrate_to_postgresql.py --backup-only
```

### Performance Monitoring
- Enable error tracking with Sentry (set `SENTRY_DSN`)
- Monitor response times via `/admin/monitoring/performance`
- Set up uptime monitoring (UptimeRobot, Pingdom)

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Errors
```bash
# Verify database URL
echo $DATABASE_URL

# Test connection
python scripts/validate_production_env.py
```

#### 2. Email Not Sending
- Verify SMTP credentials
- Check email service logs
- Test with simple script

#### 3. Static Files Not Loading
- Ensure proper file permissions
- Verify upload directory exists
- Check reverse proxy configuration

#### 4. Stripe Webhooks Failing
- Verify webhook URL is accessible
- Check webhook secret matches
- Review webhook event types

### Getting Help
1. Check application logs
2. Review monitoring dashboard
3. Verify environment variables
4. Test individual components

---

## 🔐 Security Checklist

### Production Security
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Secure session cookies enabled
- [ ] CSRF protection active
- [ ] Environment variables secured (not in code)
- [ ] Database access restricted
- [ ] Admin credentials secure
- [ ] Rate limiting configured
- [ ] Error monitoring enabled
- [ ] Regular security updates scheduled

### Stripe Security
- [ ] Using live keys (not test keys)
- [ ] Webhook endpoints secured
- [ ] Payment data not stored in application
- [ ] PCI compliance considerations addressed

---

## 📈 Scaling Considerations

### Traffic Growth
- **Railway**: Automatic scaling available
- **Render**: Configure auto-scaling in render.yaml  
- **Docker**: Use container orchestration (Kubernetes)

### Database Scaling
- **Railway**: Upgrade database plan
- **Render**: Upgrade PostgreSQL service
- **Self-hosted**: Consider read replicas

### Redis Scaling
- **Railway**: Upgrade Redis plan
- **Render**: Upgrade Redis service
- **Self-hosted**: Configure Redis clustering

---

## 🎯 Success Metrics

After deployment, verify these metrics:

- [ ] Application accessible via HTTPS
- [ ] User registration/login working
- [ ] Meal plan generation functional
- [ ] Email notifications sending
- [ ] Payment processing working
- [ ] Admin dashboard accessible
- [ ] Database backups configured
- [ ] Monitoring systems active
- [ ] Performance within acceptable ranges
- [ ] Security headers present

**Congratulations! Your Cibozer application is now production-ready! 🎉**