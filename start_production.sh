#!/bin/bash
# Production start script for Cibozer

# Exit on any error
set -e

echo "🚀 Starting Cibozer in Production Mode"

# Check for required environment variables
if [ -z "$SECRET_KEY" ]; then
    echo "❌ ERROR: SECRET_KEY environment variable is required"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is required"
    exit 1
fi

# Initialize database if needed
echo "📊 Initializing database..."
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"

# Start with Gunicorn
echo "🌐 Starting Gunicorn server..."
exec gunicorn \
    --bind 0.0.0.0:${PORT:-5000} \
    --workers ${WORKERS:-4} \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    wsgi:application