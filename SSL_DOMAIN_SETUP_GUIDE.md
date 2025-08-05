# 🔒 SSL & Domain Configuration Guide

This guide covers setting up custom domains and SSL certificates for Cibozer across different deployment platforms.

## 📋 Overview

SSL certificates and custom domains are essential for production deployment. This guide provides step-by-step instructions for:

- **Railway**: Automatic SSL with custom domains
- **Render**: Free SSL certificates with custom domains  
- **Docker/Self-hosted**: Let's Encrypt with Nginx
- **Cloudflare**: Enhanced security and performance

---

## 🚂 Railway SSL & Domain Setup

Railway provides automatic SSL certificates for custom domains.

### Step 1: Add Custom Domain
1. Go to your Railway project dashboard
2. Click on your service
3. Go to "Settings" → "Domains"
4. Click "Add Domain"
5. Enter your domain: `yourdomain.com`

### Step 2: Configure DNS
Add these DNS records with your domain provider:

```
Type: CNAME
Name: @ (or root)
Value: [railway-provided-value]

Type: CNAME  
Name: www
Value: [railway-provided-value]
```

### Step 3: Verify SSL
Railway automatically provisions SSL certificates via Let's Encrypt. This usually takes 5-10 minutes.

### Step 4: Update Application Configuration
```bash
# Set domain in Railway variables
railway variables set SERVER_NAME="yourdomain.com"
railway variables set PREFERRED_URL_SCHEME="https"
```

---

## 🎨 Render SSL & Domain Setup

Render provides free SSL certificates for all custom domains.

### Step 1: Add Custom Domain
1. Go to your Render service dashboard
2. Click "Settings"
3. Scroll to "Custom Domains"
4. Click "Add Custom Domain"
5. Enter: `yourdomain.com`

### Step 2: Configure DNS
Add these DNS records:

```
Type: CNAME
Name: @ (or yourdomain.com)
Value: [render-provided-value].onrender.com

Type: CNAME
Name: www  
Value: [render-provided-value].onrender.com
```

### Step 3: SSL Certificate
Render automatically provisions SSL certificates. No additional configuration needed.

### Step 4: Update Environment Variables
In Render dashboard, add:
```
SERVER_NAME = yourdomain.com
PREFERRED_URL_SCHEME = https
```

---

## 🐳 Docker/Self-Hosted SSL Setup

For self-hosted deployments, use Let's Encrypt with Nginx.

### Step 1: Install Certbot
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

### Step 2: Configure Domain DNS
Point your domain to your server's IP:

```
Type: A
Name: @ (or yourdomain.com)
Value: YOUR_SERVER_IP

Type: A
Name: www
Value: YOUR_SERVER_IP
```

### Step 3: Obtain SSL Certificate
```bash
# Stop nginx temporarily
sudo systemctl stop nginx

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Start nginx
sudo systemctl start nginx
```

### Step 4: Update Nginx Configuration
Edit `/etc/nginx/sites-available/cibozer`:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Include SSL security settings
    include /etc/nginx/snippets/ssl-params.conf;
    
    # Your existing location blocks...
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### Step 5: Create SSL Security Snippet
Create `/etc/nginx/snippets/ssl-params.conf`:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_dhparam /etc/nginx/dhparam.pem;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
ssl_ecdh_curve secp384r1;
ssl_session_timeout 10m;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# Security headers
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
```

### Step 6: Generate Diffie-Hellman Parameters
```bash
sudo openssl dhparam -out /etc/nginx/dhparam.pem 2048
```

### Step 7: Setup Auto-Renewal
```bash
# Add to crontab
sudo crontab -e

# Add this line for automatic renewal
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## ☁️ Cloudflare Integration

Enhance security and performance with Cloudflare.

### Step 1: Add Domain to Cloudflare
1. Sign up at [cloudflare.com](https://cloudflare.com)
2. Click "Add Site"
3. Enter your domain
4. Choose free plan
5. Update nameservers with your domain registrar

### Step 2: SSL/TLS Configuration
1. Go to SSL/TLS → Overview
2. Set encryption mode to "Full (strict)"
3. Enable "Always Use HTTPS"
4. Enable "Automatic HTTPS Rewrites"

### Step 3: Security Settings
1. **Firewall Rules**: Block suspicious traffic
2. **Rate Limiting**: Additional DDoS protection
3. **Bot Fight Mode**: Enable for bot protection
4. **Security Level**: Set to "Medium" or "High"

### Step 4: Performance Optimization
1. **Caching**: Set cache level to "Standard"
2. **Minification**: Enable CSS, JS, HTML minification
3. **Brotli**: Enable compression
4. **Polish**: Enable image optimization

### Step 5: Page Rules
Create these page rules for optimization:

```
Pattern: yourdomain.com/static/*
Settings: 
- Cache Level: Cache Everything
- Edge Cache TTL: 1 month

Pattern: yourdomain.com/api/*
Settings:
- Cache Level: Bypass
- Security Level: High

Pattern: yourdomain.com/admin/*
Settings:
- Security Level: High
- Cache Level: Bypass
```

---

## 🔧 Docker Compose with SSL

For Docker deployments with automatic SSL renewal.

### Step 1: Update Docker Compose
Create `docker-compose.ssl.yml`:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: cibozer_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/proxy_params:/etc/nginx/proxy_params:ro
      - ./nginx/ssl-params.conf:/etc/nginx/snippets/ssl-params.conf:ro
      - certbot_certs:/etc/letsencrypt:ro
      - certbot_www:/var/www/certbot:ro
    depends_on:
      - web
    networks:
      - cibozer_network

  certbot:
    image: certbot/certbot
    container_name: cibozer_certbot
    volumes:
      - certbot_certs:/etc/letsencrypt
      - certbot_www:/var/www/certbot
    command: certonly --webroot -w /var/www/certbot --force-renewal --email your-email@example.com -d yourdomain.com -d www.yourdomain.com --agree-tos

volumes:
  certbot_certs:
  certbot_www:
```

### Step 2: Initial Certificate Generation
```bash
# Start services without SSL first
docker-compose -f docker-compose.yml -f docker-compose.ssl.yml up -d nginx

# Generate initial certificates
docker-compose -f docker-compose.ssl.yml run --rm certbot

# Restart nginx with SSL
docker-compose -f docker-compose.ssl.yml restart nginx
```

### Step 3: Auto-Renewal Setup
Create renewal script `scripts/renew_ssl.sh`:

```bash
#!/bin/bash
cd /path/to/your/project
docker-compose -f docker-compose.ssl.yml run --rm certbot renew
docker-compose -f docker-compose.ssl.yml restart nginx
```

Add to crontab:
```bash
0 12 * * * /path/to/your/project/scripts/renew_ssl.sh
```

---

## 🧪 Testing SSL Configuration

### Step 1: SSL Labs Test
Test your SSL configuration at: https://www.ssllabs.com/ssltest/

Target grade: **A** or **A+**

### Step 2: Security Headers Test
Test security headers at: https://securityheaders.com/

Target grade: **A** or **A+**

### Step 3: Manual Verification
```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Test HTTP to HTTPS redirect
curl -I http://yourdomain.com

# Test security headers
curl -I https://yourdomain.com
```

---

## 🚨 Troubleshooting

### Common SSL Issues

#### 1. Certificate Not Valid
- **Problem**: Browser shows "Not Secure"
- **Solution**: Check certificate installation and domain matching

#### 2. Mixed Content Warnings
- **Problem**: HTTP resources on HTTPS page
- **Solution**: Update all URLs to use HTTPS or relative paths

#### 3. Redirect Loops
- **Problem**: Infinite redirects between HTTP/HTTPS
- **Solution**: Check proxy headers and application configuration

#### 4. Certificate Renewal Fails
- **Problem**: Let's Encrypt renewal errors
- **Solution**: Check DNS, firewall, and domain validation

### Debugging Commands

```bash
# Check certificate expiry
openssl x509 -in /path/to/cert.pem -text -noout | grep "Not After"

# Test SSL connection
openssl s_client -connect yourdomain.com:443

# Check nginx configuration
nginx -t

# View SSL certificate details
curl -vI https://yourdomain.com 2>&1 | grep -A 10 "Server certificate"
```

---

## 📊 SSL Configuration Checklist

### Pre-Production
- [ ] Domain DNS configured correctly
- [ ] SSL certificate obtained and installed
- [ ] HTTP to HTTPS redirect working
- [ ] Security headers configured
- [ ] SSL Labs grade A or A+
- [ ] Security headers grade A or A+

### Production
- [ ] SSL certificate auto-renewal configured
- [ ] Monitoring setup for certificate expiry
- [ ] Security headers properly configured
- [ ] Content Security Policy (CSP) configured
- [ ] HTTP Strict Transport Security (HSTS) enabled
- [ ] Secure cookie settings enabled

### Performance
- [ ] HTTP/2 enabled
- [ ] Gzip/Brotli compression enabled
- [ ] Static file caching configured
- [ ] CDN integration (if using Cloudflare)

---

## 🎯 Security Best Practices

### SSL/TLS Configuration
- Use TLS 1.2 and 1.3 only
- Disable weak cipher suites
- Enable HTTP Strict Transport Security (HSTS)
- Implement Certificate Transparency monitoring

### Application Security
- Set secure session cookies
- Implement Content Security Policy (CSP)
- Enable X-Frame-Options protection
- Use X-Content-Type-Options: nosniff

### Infrastructure Security
- Regular security updates
- Firewall configuration
- Rate limiting
- DDoS protection (via Cloudflare)

**Your Cibozer application is now secured with SSL and ready for production traffic! 🔒**