#!/bin/bash
set -e

# Entrypoint script for Arete Reflex application
# Handles initialization, health checks, and graceful startup

# Colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Environment validation
validate_environment() {
    log_info "Validating environment configuration..."
    
    # Check required environment variables
    REQUIRED_VARS=(
        "ENVIRONMENT"
        "NEO4J_URI"
        "WEAVIATE_URL"
    )
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            log_warn "Environment variable $var not set, using defaults"
        else
            log_info "$var is configured"
        fi
    done
    
    # Validate environment type
    if [ "${ENVIRONMENT}" = "production" ]; then
        log_info "Running in PRODUCTION mode"
        
        # Additional production checks
        if [ -z "${SECRET_KEY}" ]; then
            log_error "SECRET_KEY must be set in production!"
            exit 1
        fi
        
        if [ -z "${DATABASE_URL}" ]; then
            log_error "DATABASE_URL must be set in production!"
            exit 1
        fi
        
    elif [ "${ENVIRONMENT}" = "staging" ]; then
        log_info "Running in STAGING mode"
        
    elif [ "${ENVIRONMENT}" = "development" ]; then
        log_info "Running in DEVELOPMENT mode"
        
    else
        log_warn "Unknown ENVIRONMENT: ${ENVIRONMENT}, defaulting to development"
        export ENVIRONMENT="development"
    fi
}

# Database connectivity check
check_database_connectivity() {
    log_info "Checking database connectivity..."
    
    if [ -n "${DATABASE_URL}" ]; then
        # Extract host and port from DATABASE_URL
        # This is a simplified check - in production you'd use proper tools
        log_info "Database URL configured: ${DATABASE_URL}"
    fi
    
    # Check Neo4j connectivity
    if [ -n "${NEO4J_URI}" ]; then
        log_info "Neo4j URI configured: ${NEO4J_URI}"
        # In production, add actual connectivity test here
    fi
    
    # Check Weaviate connectivity
    if [ -n "${WEAVIATE_URL}" ]; then
        log_info "Weaviate URL configured: ${WEAVIATE_URL}"
        # In production, add actual connectivity test here
    fi
}

# Initialize application
initialize_application() {
    log_info "Initializing Arete application..."
    
    # Create necessary directories
    mkdir -p /app/logs
    mkdir -p /app/tmp
    mkdir -p /app/.web
    
    # Set proper permissions
    chmod 755 /app/logs
    chmod 755 /app/tmp
    
    log_success "Application directories created"
}

# Reflex-specific initialization
initialize_reflex() {
    log_info "Initializing Reflex application..."
    
    cd /app
    
    # Initialize Reflex if not already done
    if [ ! -f ".web/reflex.json" ]; then
        log_info "Running reflex init..."
        reflex init --template=blank || {
            log_error "Failed to initialize Reflex"
            exit 1
        }
    else
        log_info "Reflex already initialized"
    fi
    
    # Export frontend if in production
    if [ "${ENVIRONMENT}" = "production" ]; then
        log_info "Exporting frontend for production..."
        reflex export --frontend-only --no-zip || {
            log_warn "Frontend export failed, continuing anyway"
        }
    fi
    
    log_success "Reflex initialization complete"
}

# Health check function
health_check() {
    log_info "Running health checks..."
    
    # Check if application is responsive
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then
            log_success "Health check passed"
            return 0
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, retrying in 2s..."
        sleep 2
        ((attempt++))
    done
    
    log_error "Health checks failed after $max_attempts attempts"
    return 1
}

# Cleanup function for graceful shutdown
cleanup() {
    log_info "Received shutdown signal, cleaning up..."
    
    # Kill background processes gracefully
    if [ -n "$REFLEX_PID" ]; then
        log_info "Stopping Reflex backend (PID: $REFLEX_PID)..."
        kill -TERM "$REFLEX_PID" 2>/dev/null || true
        wait "$REFLEX_PID" 2>/dev/null || true
    fi
    
    if [ -n "$FRONTEND_PID" ]; then
        log_info "Stopping frontend server (PID: $FRONTEND_PID)..."
        kill -TERM "$FRONTEND_PID" 2>/dev/null || true
        wait "$FRONTEND_PID" 2>/dev/null || true
    fi
    
    log_info "Cleanup completed"
    exit 0
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGTERM SIGINT SIGQUIT

# Main execution
main() {
    log_info "Starting Arete Reflex application..."
    log_info "Container started at $(date)"
    
    # Run initialization steps
    validate_environment
    check_database_connectivity
    initialize_application
    initialize_reflex
    
    # Determine run mode
    case "${1:-reflex}" in
        "reflex")
            log_info "Starting Reflex application..."
            exec reflex run --env "${ENVIRONMENT}" --backend-port 8000 --frontend-port 3000
            ;;
        "backend-only")
            log_info "Starting backend only..."
            exec reflex run --env "${ENVIRONMENT}" --backend-only --backend-port 8000
            ;;
        "frontend-only")
            log_info "Starting frontend only..."
            exec reflex run --env "${ENVIRONMENT}" --frontend-only --frontend-port 3000
            ;;
        "production")
            log_info "Starting production server..."
            # Start backend
            reflex run --env production --backend-only --backend-port 8000 &
            REFLEX_PID=$!
            
            # Wait for backend to be ready
            sleep 10
            
            # Start frontend (if not using external web server)
            if [ "${USE_EXTERNAL_FRONTEND}" != "true" ]; then
                reflex run --env production --frontend-only --frontend-port 3000 &
                FRONTEND_PID=$!
            fi
            
            # Wait for processes
            wait
            ;;
        "health-check")
            health_check
            exit $?
            ;;
        "shell")
            log_info "Starting interactive shell..."
            exec /bin/bash
            ;;
        *)
            log_info "Starting with custom command: $*"
            exec "$@"
            ;;
    esac
}

# Execute main function
main "$@"