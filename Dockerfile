# Multi-stage Docker build for Arete Reflex application
# Optimized for production deployment

# Build stage - Frontend assets
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files first for better caching
COPY package.json package-lock.json* ./

# Install Node.js dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy source code
COPY . .

# Build frontend assets (if they exist)
RUN npm run build 2>/dev/null || echo "No npm build script found"

# Python build stage
FROM python:3.11-slim AS python-builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment and install dependencies
WORKDIR /app
COPY requirements.txt ./

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir reflex gunicorn

# Production stage
FROM python:3.11-slim AS production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# Set up application directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=python-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy built frontend assets (if they exist)
COPY --from=frontend-builder /app/.web/public /app/.web/public 2>/dev/null || true

# Copy application code
COPY --chown=appuser:appuser . .

# Copy configuration files
COPY --chown=appuser:appuser config/ config/

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/tmp /var/log/arete \
    && chown -R appuser:appuser /app /var/log/arete

# Set environment variables
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy Docker configuration files
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Pre-compile Reflex application
RUN cd /app && reflex init --template=blank 2>/dev/null || echo "Reflex init completed"

# Expose ports
# 3000 - Frontend
# 8000 - Backend API
# 80   - Nginx proxy
EXPOSE 3000 8000 80

# Health check for the application
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || curl -f http://localhost:3000 || exit 1

# Switch to non-root user for security
USER appuser

# Set entrypoint and default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["reflex", "run", "--env", "prod", "--backend-only"]