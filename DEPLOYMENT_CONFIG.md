# Cibozer Deployment Configuration Guide

## Critical Environment Variables

The following environment variables MUST be set for production deployment:

### 1. SECRET_KEY (REQUIRED)
Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Then set it in your deployment platform:
- **Heroku**: `heroku config:set SECRET_KEY="your-generated-key"`
- **Vercel**: Add to environment variables in project settings
- **Railway**: Add to environment variables in service settings
- **Local**: `export SECRET_KEY="your-generated-key"`

### 2. Stripe API Keys (REQUIRED for payments)
Get your keys from [Stripe Dashboard](https://dashboard.stripe.com/apikeys)

```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
```

⚠️ **WARNING**: Never use test keys in production!

### 3. Database Configuration
```bash
DATABASE_URL=postgresql://user:password@host:port/dbname
```

Default uses SQLite (not recommended for production).

### 4. Optional Configuration
```bash
FLASK_ENV=production
DEBUG=False
ADMIN_EMAIL=admin@cibozer.com
ADMIN_PASSWORD=<secure-password>
```

## Deployment Checklist

- [ ] Set SECRET_KEY environment variable
- [ ] Configure Stripe API keys
- [ ] Set up production database
- [ ] Configure admin credentials
- [ ] Enable HTTPS/SSL
- [ ] Test payment flow
- [ ] Verify email functionality

## Security Notes

1. Never commit .env files to version control
2. Use different keys for development and production
3. Rotate SECRET_KEY periodically
4. Monitor Stripe webhook endpoints
5. Enable 2FA for admin accounts