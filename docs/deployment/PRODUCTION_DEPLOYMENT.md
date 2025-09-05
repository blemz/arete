# Production Deployment Guide - Arete Reflex Application

## Overview

This guide covers the complete production deployment setup for the Arete Classical Philosophy Chat application, built with Reflex, including testing infrastructure, quality assurance, and deployment automation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Production Configuration](#production-configuration)
4. [Testing Infrastructure](#testing-infrastructure)
5. [Quality Assurance](#quality-assurance)
6. [Docker Deployment](#docker-deployment)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Monitoring and Observability](#monitoring-and-observability)
9. [Security](#security)
10. [Maintenance](#maintenance)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ LTS recommended) or macOS
- **Python**: 3.11+
- **Node.js**: 20.x LTS
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Memory**: Minimum 8GB RAM, Recommended 16GB+
- **Storage**: Minimum 50GB, Recommended 100GB+ SSD
- **CPU**: Minimum 4 cores, Recommended 8+ cores

### External Services

- **PostgreSQL**: 15+ (for application data)
- **Neo4j**: 5.11+ Community/Enterprise (for knowledge graphs)
- **Weaviate**: 1.21+ (for vector embeddings)
- **Redis**: 7+ (for caching and session storage)
- **Nginx**: 1.20+ (for reverse proxy and load balancing)

### Domain and SSL

- Registered domain name
- SSL certificate (Let's Encrypt recommended for free SSL)
- DNS configuration access

## Environment Setup

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y git curl wget unzip software-properties-common

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-dev python3.11-venv python3-pip
```

### 2. Application Deployment Directory

```bash
# Create application directory
sudo mkdir -p /opt/arete
sudo chown $USER:$USER /opt/arete
cd /opt/arete

# Clone the repository
git clone https://github.com/your-org/arete.git .

# Create necessary directories
mkdir -p logs data backups ssl
```

### 3. Environment Variables

Create production environment file:

```bash
# /opt/arete/.env.production
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-here
DEBUG=false

# Database Configuration
DATABASE_URL=postgresql://arete_user:secure_password@postgres:5432/arete_prod
REDIS_URL=redis://:redis_password@redis:6379/0

# Graph Database
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secure_neo4j_password

# Vector Database
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_API_KEY=your-weaviate-api-key
WEAVIATE_API_USER=arete-prod

# AI Services
OPENAI_API_KEY=sk-your-openai-api-key
EMBEDDING_PROVIDER=openai
KG_LLM_PROVIDER=openai

# Application Settings
FRONTEND_PORT=3000
BACKEND_PORT=8000
WORKER_PROCESSES=4
MAX_REQUESTS=1000

# Security
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
SESSION_TIMEOUT=3600
RATE_LIMIT=60
BURST_LIMIT=100

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_ENABLED=true
GRAFANA_PASSWORD=secure_grafana_password

# SSL Configuration
SSL_CERT_PATH=/opt/arete/ssl/cert.pem
SSL_KEY_PATH=/opt/arete/ssl/key.pem

# Backup Configuration
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
```

## Production Configuration

### 1. Reflex Configuration

The production configuration is managed in `config/production_rxconfig.py`:

```python
# Key production settings
config = rx.Config(
    app_name="arete",
    environment="production",
    debug=False,
    
    # Performance optimizations
    compile_timeout=180,
    worker_processes=4,
    max_requests=1000,
    enable_compression=True,
    enable_caching=True,
    
    # Security settings
    secure_cookies=True,
    csrf_protection=True,
    force_https=True,
    
    # Database connections
    db_url=get_database_url(),
    redis_url=get_redis_config(),
)
```

### 2. Nginx Configuration

Create `/opt/arete/docker/nginx/nginx.conf`:

```nginx
upstream arete_backend {
    server arete-app:8000;
}

upstream arete_frontend {
    server arete-app:3000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Frontend (static assets and main app)
    location / {
        proxy_pass http://arete_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://arete_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check
    location /health {
        proxy_pass http://arete_backend/health;
        access_log off;
    }
    
    # Static assets with caching
    location /static/ {
        alias /opt/arete/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Testing Infrastructure

### 1. Test Execution

Run the complete test suite:

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run specific test categories
pytest tests/unit/              # Unit tests
pytest tests/reflex/            # Reflex component tests  
pytest tests/integration/       # Integration tests
pytest tests/e2e/              # End-to-end tests

# Run with coverage
pytest --cov=arete --cov-report=html
```

### 2. Performance Testing

```bash
# Load testing with Locust
locust -f tests/performance/locustfile.py --host=http://localhost:3000

# Memory profiling
python -m memory_profiler your_script.py

# Performance benchmarking
python scripts/benchmark_performance.py
```

### 3. Accessibility Testing

```bash
# Install accessibility tools
npm install -g axe-core pa11y-ci

# Run accessibility tests
axe http://localhost:3000
pa11y-ci --sitemap http://localhost:3000/sitemap.xml
```

## Quality Assurance

### 1. Pre-commit Hooks

Set up automated quality checks:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

### 2. Code Quality Tools

```bash
# Code formatting
black arete/
isort arete/

# Linting
flake8 arete/
ruff check arete/

# Type checking  
mypy arete/

# Security scanning
bandit -r arete/
safety check
```

## Docker Deployment

### 1. Build and Deploy

```bash
# Build the application
docker-compose -f docker/docker-compose.prod.yml build

# Deploy with all services
docker-compose -f docker/docker-compose.prod.yml up -d

# View logs
docker-compose -f docker/docker-compose.prod.yml logs -f arete-app

# Scale the application
docker-compose -f docker/docker-compose.prod.yml up -d --scale arete-app=3
```

### 2. Database Initialization

```bash
# Initialize databases
docker-compose exec arete-app python scripts/init_database.py

# Run migrations
docker-compose exec arete-app alembic upgrade head

# Load initial data
docker-compose exec arete-app python scripts/load_initial_data.py
```

### 3. SSL Certificate Setup

```bash
# Using Let's Encrypt with Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal (already set up by certbot)
sudo crontab -l | grep certbot
```

## CI/CD Pipeline

### 1. GitHub Actions Setup

The CI/CD pipeline is configured in `.github/workflows/ci-cd.yml` and includes:

- **Code Quality**: Black, isort, flake8, mypy, bandit
- **Testing**: Unit, integration, E2E, accessibility, performance
- **Security**: Vulnerability scanning, container security
- **Build**: Multi-platform Docker images
- **Deploy**: Automated deployment to staging/production

### 2. Deployment Triggers

- **Staging**: Automatic deployment on `develop` branch push
- **Production**: Automatic deployment on `main` branch push after all tests pass
- **Manual**: Workflow dispatch for emergency deployments

### 3. Rollback Strategy

```bash
# Quick rollback using Docker tags
docker-compose -f docker/docker-compose.prod.yml pull arete-app:previous
docker-compose -f docker/docker-compose.prod.yml up -d

# Database rollback
docker-compose exec postgres psql -U arete_user -d arete_prod -c "SELECT version FROM alembic_version;"
docker-compose exec arete-app alembic downgrade -1
```

## Monitoring and Observability

### 1. Application Monitoring

- **Prometheus**: Metrics collection on port 9090
- **Grafana**: Dashboard and visualization on port 3001  
- **Loki**: Log aggregation on port 3100
- **Alertmanager**: Alert routing and management

### 2. Key Metrics to Monitor

```yaml
# Custom application metrics
- rag_query_duration_seconds
- rag_query_success_rate  
- active_conversations
- citation_accuracy_score
- user_satisfaction_rating
- database_connection_pool_usage
- cache_hit_ratio
- memory_usage_percentage
- cpu_usage_percentage
```

### 3. Health Checks

```bash
# Application health
curl -f http://localhost:8000/health

# Database connectivity  
curl -f http://localhost:8000/health/database

# RAG service health
curl -f http://localhost:8000/health/rag
```

## Security

### 1. Security Best Practices

- **HTTPS**: Force SSL/TLS encryption
- **HSTS**: HTTP Strict Transport Security headers
- **CSP**: Content Security Policy headers
- **CSRF**: Cross-Site Request Forgery protection
- **Rate Limiting**: API and UI request limiting
- **WAF**: Web Application Firewall (Cloudflare/AWS WAF)

### 2. Security Monitoring

```bash
# Container security scanning
docker scan arete-app:latest

# Vulnerability assessment
nmap -sV -O your-domain.com

# SSL/TLS testing
sslyze --regular your-domain.com
```

### 3. Backup and Recovery

```bash
# Database backup script
#!/bin/bash
BACKUP_DIR="/opt/arete/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
docker-compose exec postgres pg_dump -U arete_user arete_prod > $BACKUP_DIR/postgres_$DATE.sql

# Neo4j backup
docker-compose exec neo4j neo4j-admin database dump --to-path=/backups neo4j > $BACKUP_DIR/neo4j_$DATE.dump

# Weaviate backup
curl -X POST "http://localhost:8080/v1/backups" -H "Content-Type: application/json" -d '{"id": "backup_'$DATE'"}'
```

## Maintenance

### 1. Regular Maintenance Tasks

```bash
# Weekly maintenance script
#!/bin/bash

# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean Docker resources
docker system prune -f

# Rotate logs
logrotate /opt/arete/logs/logrotate.conf

# Update SSL certificates
certbot renew --quiet

# Database maintenance
docker-compose exec postgres vacuumdb -U arete_user -d arete_prod --analyze --verbose

# Restart services if needed
docker-compose -f docker/docker-compose.prod.yml restart
```

### 2. Performance Optimization

```bash
# Database query optimization
docker-compose exec postgres psql -U arete_user -d arete_prod -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Cache optimization
redis-cli --latency-history -i 1

# Application profiling
python -m cProfile -o profile.stats your_script.py
```

## Troubleshooting

### 1. Common Issues

**Application Won't Start:**
```bash
# Check logs
docker-compose logs arete-app

# Check configuration
docker-compose config

# Verify environment variables
docker-compose exec arete-app env | grep -E "(DATABASE|REDIS|NEO4J|WEAVIATE)"
```

**Database Connection Issues:**
```bash
# Test PostgreSQL connection
docker-compose exec postgres psql -U arete_user -d arete_prod -c "SELECT 1;"

# Test Neo4j connection
docker-compose exec neo4j cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1;"

# Test Weaviate connection
curl http://localhost:8080/v1/meta
```

**Performance Issues:**
```bash
# Check resource usage
docker stats

# Check database performance
docker-compose exec postgres psql -U arete_user -d arete_prod -c "SELECT * FROM pg_stat_activity;"

# Check application metrics
curl http://localhost:9090/metrics | grep arete
```

### 2. Emergency Procedures

**Service Outage:**
1. Check service status: `systemctl status docker`
2. Restart services: `docker-compose restart`
3. Check logs for errors: `docker-compose logs --tail=100`
4. Implement temporary fallback if needed
5. Notify stakeholders via monitoring alerts

**Security Incident:**
1. Isolate affected systems
2. Review access logs: `grep "suspicious_pattern" /var/log/nginx/access.log`
3. Change all secrets and API keys
4. Update security rules
5. Conduct post-incident review

### 3. Support and Documentation

- **Application Logs**: `/opt/arete/logs/`
- **System Logs**: `/var/log/syslog`
- **Service Logs**: `journalctl -u docker`
- **Monitoring Dashboards**: `https://your-domain.com:3001` (Grafana)
- **Metrics**: `https://your-domain.com:9090` (Prometheus)

## Migration from Streamlit to Reflex

### Key Differences

1. **Architecture**: Streamlit's server-side rendering vs Reflex's client-server architecture
2. **State Management**: Streamlit's session state vs Reflex's reactive state management
3. **Components**: Streamlit widgets vs Reflex components
4. **Deployment**: Single container vs multi-service architecture

### Migration Checklist

- [ ] Update component structure from Streamlit to Reflex
- [ ] Migrate state management logic
- [ ] Update styling from Streamlit themes to Tailwind CSS
- [ ] Implement proper error boundaries
- [ ] Update testing infrastructure
- [ ] Configure production environment
- [ ] Set up CI/CD pipeline
- [ ] Implement monitoring and logging
- [ ] Conduct security review
- [ ] Performance testing and optimization
- [ ] User acceptance testing
- [ ] Documentation update
- [ ] Team training on Reflex

---

This production deployment guide ensures a robust, scalable, and secure deployment of the Arete Reflex application with comprehensive testing, quality assurance, and monitoring capabilities.