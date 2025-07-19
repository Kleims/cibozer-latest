#!/usr/bin/env python3
"""
Stripe Configuration Setup Script
Helps validate and set up Stripe integration for Cibozer
"""

import os
import sys
import io
from dotenv import load_dotenv

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    import stripe
except ImportError:
    print("ERROR: Stripe module not installed. Run: pip install stripe")
    sys.exit(1)

# Load environment variables
load_dotenv()

def check_stripe_config():
    """Check and validate Stripe configuration"""
    print("=== Cibozer Stripe Configuration Check ===\n")
    
    # Check for API keys
    secret_key = os.getenv('STRIPE_SECRET_KEY', '')
    publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
    
    issues = []
    
    # Validate secret key
    if not secret_key:
        issues.append("X STRIPE_SECRET_KEY not set")
    elif secret_key.startswith('sk_test_'):
        print("! Using TEST Stripe secret key (ok for development)")
    elif secret_key.startswith('sk_live_'):
        print("✓ Using LIVE Stripe secret key")
    elif 'your_stripe_secret_key' in secret_key:
        issues.append("X STRIPE_SECRET_KEY still has placeholder value")
    else:
        issues.append("X STRIPE_SECRET_KEY format unrecognized")
    
    # Validate publishable key
    if not publishable_key:
        issues.append("X STRIPE_PUBLISHABLE_KEY not set")
    elif publishable_key.startswith('pk_test_'):
        print("! Using TEST Stripe publishable key (ok for development)")
    elif publishable_key.startswith('pk_live_'):
        print("✓ Using LIVE Stripe publishable key")
    elif 'your_stripe_publishable_key' in publishable_key:
        issues.append("X STRIPE_PUBLISHABLE_KEY still has placeholder value")
    else:
        issues.append("X STRIPE_PUBLISHABLE_KEY format unrecognized")
    
    # Check webhook secret
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    if not webhook_secret:
        print("! STRIPE_WEBHOOK_SECRET not set (required for webhooks)")
    else:
        print("✓ STRIPE_WEBHOOK_SECRET is configured")
    
    # Check price IDs
    price_pro = os.getenv('STRIPE_PRICE_ID_PRO', '')
    price_premium = os.getenv('STRIPE_PRICE_ID_PREMIUM', '')
    
    if not price_pro or 'your' in price_pro:
        issues.append("X STRIPE_PRICE_ID_PRO not configured")
    else:
        print("✓ Pro plan price ID configured")
        
    if not price_premium or 'your' in price_premium:
        issues.append("X STRIPE_PRICE_ID_PREMIUM not configured")
    else:
        print("✓ Premium plan price ID configured")
    
    # Test API connection if keys are valid
    if secret_key and not any('secret_key' in issue for issue in issues):
        print("\n> Testing Stripe API connection...")
        try:
            stripe.api_key = secret_key
            # Try to list products (minimal API call)
            stripe.Product.list(limit=1)
            print("✓ Successfully connected to Stripe API")
        except stripe.error.AuthenticationError:
            issues.append("X Stripe authentication failed - check your API key")
        except Exception as e:
            issues.append(f"X Stripe connection error: {str(e)}")
    
    # Summary
    print("\n=== Configuration Summary ===")
    if issues:
        print("\n! Issues found:")
        for issue in issues:
            print(f"  {issue}")
        print("\n> Next steps:")
        print("1. Get your API keys from https://dashboard.stripe.com/apikeys")
        print("2. Set environment variables:")
        print("   - STRIPE_SECRET_KEY=sk_live_...")
        print("   - STRIPE_PUBLISHABLE_KEY=pk_live_...")
        print("3. Create products and price IDs in Stripe Dashboard")
        print("4. Update STRIPE_PRICE_ID_PRO and STRIPE_PRICE_ID_PREMIUM")
        return False
    else:
        print("\n✓ All Stripe configuration looks good!")
        return True

if __name__ == "__main__":
    success = check_stripe_config()
    sys.exit(0 if success else 1)