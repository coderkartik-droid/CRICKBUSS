# ==========================================
# CrickScore Live - Production Dockerfile
# Python 3.13 ASGI (Daphne / WebSockets)
# ==========================================

FROM python:3.13-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install python requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Create directory for static & media files
RUN mkdir -p /app/staticfiles /app/media

# Collect static files with dummy key
RUN python manage.py collectstatic --noinput --clear || true

# Expose Daphne ASGI port
EXPOSE 8000

# Default entrypoint starts Daphne ASGI server
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
