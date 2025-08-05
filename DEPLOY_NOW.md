# 🚀 Deploy to Railway - Step by Step Guide

## Prerequisites
You'll need:
1. A GitHub account
2. Your code pushed to GitHub
3. A Railway account (free)

---

## Step 1: Push Your Code to GitHub

### If you haven't already:
```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "MVP Week 1: Ready for deployment - all core features working"

# Create a new repository on GitHub.com, then:
git remote add origin https://github.com/YOUR_USERNAME/cibozer.git
git branch -M main
git push -u origin main
```

---

## Step 2: Sign Up for Railway

1. Go to **[railway.app](https://railway.app)**
2. Click **"Start a New Project"**
3. Sign in with GitHub (recommended)

---

## Step 3: Deploy from GitHub

1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your **cibozer** repository
4. Railway will automatically detect it's a Python app

---

## Step 4: Add PostgreSQL Database

1. In your Railway project, click **"New"**
2. Select **"Database"** → **"PostgreSQL"**
3. It will automatically connect to your app

---

## Step 5: Set Environment Variables

Click on your app service, then go to **Variables** tab and add:

```env
# REQUIRED - Generate a secure key
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random

# Optional but recommended
FLASK_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# Email (optional - for password reset)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Admin (optional)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=SecureAdminPass123!
```

### To generate a secure SECRET_KEY:
```python
# Run this in Python:
import secrets
print(secrets.token_hex(32))
```

---

## Step 6: Deploy!

1. Railway will automatically deploy when you:
   - Push to GitHub
   - Change environment variables
   - Click "Redeploy"

2. Wait for the build to complete (2-3 minutes)

3. Click on your deployment to get your URL:
   - It will look like: `cibozer-production.up.railway.app`

---

## Step 7: Test Your Production Site

Once deployed, test these critical paths:

### 1. Check Homepage
```
https://your-app.up.railway.app/
```

### 2. Register a Test User
```
https://your-app.up.railway.app/auth/register
```

### 3. Create a Meal Plan
- Login with test user
- Click "Create Meal Plan"
- Generate a plan
- Save it
- View saved plans

---

## Step 8: Monitor Your App

### In Railway Dashboard:
- **Logs**: View real-time logs
- **Metrics**: Monitor CPU, memory, requests
- **Database**: Check connections and queries

### Common Issues & Fixes:

**App Crashes on Start:**
- Check logs for missing environment variables
- Ensure SECRET_KEY is set
- Check DATABASE_URL is connected

**500 Errors:**
- Check logs for specific error
- Usually missing dependencies or env vars

**Slow Performance:**
- Upgrade from free tier if needed
- Check database queries in logs

---

## Step 9: Update MVP Tracker

Once deployed successfully:

```bash
# Run locally:
python mvp_dashboard.py update production_deployed=true
```

---

## 🎉 Congratulations!

Your app is now live! Share your URL:
- `https://your-app.up.railway.app`

### Next Steps:
1. Share with 5 friends/family for testing
2. Fix any issues they find
3. Move to MVP Week 2: Make It Usable

---

## Alternative: Quick Deploy with Railway CLI

If you prefer command line:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Deploy
railway up

# Open in browser
railway open
```

---

## Need Help?

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Common issues: Check the logs first!

---

**Remember: The goal is to get it deployed, not perfect. Deploy now, improve later!**