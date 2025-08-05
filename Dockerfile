# ==============================================
# Cibozer Production Dockerfile
# Multi-stage build for optimized production deployment
# ==============================================

# Stage 1: Build dependencies and prepare application
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION
ARG VCS_REF

# Labels for image metadata
LABEL maintainer="Cibozer Team"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.name="cibozer"
LABEL org.label-schema.description="AI-powered meal planning application"
LABEL org.label-schema.url="https://cibozer.com"
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.version=$VERSION
LABEL org.label-schema.schema-version="1.0"

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================
# Stage 2: Production runtime
FROM python:3.11-slim as production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r cibozer && useradd -r -g cibozer cibozer

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs static/uploads static/pdfs static/videos instance backups && \
    chown -R cibozer:cibozer /app

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check script
COPY --chown=cibozer:cibozer <<EOF /app/healthcheck.py
#!/usr/bin/env python3
import sys
import requests
import os

def health_check():
    try:
        port = os.environ.get('PORT', '5000')
        response = requests.get(f'http://localhost:{port}/api/health', timeout=10)
        if response.status_code == 200:
            return 0
        else:
            print(f"Health check failed: {response.status_code}")
            return 1
    except Exception as e:
        print(f"Health check error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(health_check())
EOF

# Make healthcheck script executable
RUN chmod +x /app/healthcheck.py

# Switch to non-root user
USER cibozer

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python /app/healthcheck.py || exit 1

# Production startup command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--worker-class", "sync", "--worker-connections", "1000", "--timeout", "120", "--keepalive", "5", "--max-requests", "1000", "--max-requests-jitter", "100", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", "wsgi:application"]

# ==============================================
# Stage 3: Development variant (optional)
FROM production as development

# Switch back to root to install dev dependencies
USER root

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-cov black flake8 mypy

# Install additional development tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Switch back to cibozer user
USER cibozer

# Development command (override in docker-compose)
CMD ["python", "wsgi.py"]