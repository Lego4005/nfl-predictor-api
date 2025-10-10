#!/bin/bash

# Expert Council Betting System - Quick Start Script
# Thisutomates the initial setup and deployment process

set -e  # Exit on any error

echo "🚀 Expert Council Betting System - Quick Start"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if required commands exist
check_dependencies() {
    print_info "Checking dependencies..."

    commands=("node" "npm" "python3" "pip" "docker" "docker-compose" "curl")
    missing_commands=()

    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            missing_commands+=($cmd)
        fi
    done

    if [ ${#missing_commands[@]} -ne 0 ]; then
        print_error "Missing required commands: ${missing_commands[*]}"
        print_info "Please install the missing dependencies and run this script again."
        exit 1
    fi

    print_status "All dependencies found"
}

# Setup environment files
setup_environment() {
    print_info "Setting up environment files..."

    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            print_status "Created .env from template"
            print_warning "Please edit .env with your API keys and configuration"
        else
            print_error ".env.example not found. Please create .env manually."
            exit 1
        fi
    else
        print_status ".env already exists"
    fi

    # Check if critical environment variables are set
    if [ -f .env ]; then
        source .env

        missing_vars=()
        required_vars=("SUPABASE_URL" "SUPABASE_ANON_KEY" "SUPABASE_SERVICE_ROLE_KEY")

        for var in "${required_vars[@]}"; do
            if [ -z "${!var}" ]; then
                missing_vars+=($var)
            fi
        done

        if [ ${#missing_vars[@]} -ne 0 ]; then
            print_warning "Missing required environment variables: ${missing_vars[*]}"
            print_info "Please update your .env file with these values"
        else
            print_status "Required environment variables are set"
        fi
    fi
}

# Install dependencies
install_dependencies() {
    print_info "Installing dependencies..."

    # Node.js dependencies
    if [ -f package.json ]; then
        print_info "Installing Node.js dependencies..."
        npm install
        print_status "Node.js dependencies installed"
    fi

    # Python dependencies
    if [ -f requirements.txt ]; then
        print_info "Installing Python dependencies..."

        # Create virtual environment if it doesn't exist
        if [ ! -d venv ]; then
            python3 -m venv venv
            print_status "Created Python virtual environment"
        fi

        # Activate virtual environment and install dependencies
        source venv/bin/activate
        pip install -r requirements.txt

        if [ -f requirements-ml.txt ]; then
            pip install -r requirements-ml.txt
        fi

        print_status "Python dependencies installed"
    fi
}

# Setup database
setup_database() {
    print_info "Setting up database..."

    # Check if Supabase CLI is installed
    if ! command -v supabase &> /dev/null; then
        print_warning "Supabase CLI not found. Installing..."
        npm install -g supabase
    fi

    # Check if we can connect to Supabase
    if [ -n "$SUPABASE_URL" ] && [ -n "$SUPABASE_ANON_KEY" ]; then
        print_info "Testing database connection..."

        # Simple connection test using curl
        response=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "apikey: $SUPABASE_ANON_KEY" \
            -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
            "$SUPABASE_URL/rest/v1/")

        if [ "$response" = "200" ]; then
            print_status "Database connection successful"
        else
            print_warning "Database connection failed (HTTP $response)"
            print_info "Please check your Supabase configuration"
        fi
    else
        print_warning "Supabase configuration not found in .env"
    fi
}

# Start services
start_services() {
    print_info "Starting services..."

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi

    # Start services with Docker Compose
    if [ -f docker-compose.yml ]; then
        print_info "Starting services with Docker Compose..."
        docker-compose up -d --build

        # Wait a moment for services to start
        sleep 10

        # Check service status
        if docker-compose ps | grep -q "Up"; then
            print_status "Services started successfully"
        else
            print_warning "Some services may not have started correctly"
            print_info "Check service status with: docker-compose ps"
        fi
    else
        print_warning "docker-compose.yml not found. Starting services manually..."

        # Start FastAPI server in background
        if [ -f src/api/main.py ]; then
            source venv/bin/activate
            nohup uvicorn src.api.main:app --reload --port 8000 > api.log 2>&1 &
            print_status "FastAPI server started on port 8000"
        fi

        # Start WebSocket server in background
        if [ -f src/websocket/server.js ]; then
            nohup node src/websocket/server.js > websocket.log 2>&1 &
            print_status "WebSocket server started on port 8080"
        fi
    fi
}

# Run health checks
run_health_checks() {
    print_info "Running health checks..."

    # Wait for services to be ready
    sleep 5

    # Check API health
    api_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
    if [ "$api_health" = "200" ]; then
        print_status "API health check passed"
    else
        print_warning "API health check failed (HTTP $api_health)"
    fi

    # Check WebSocket server
    if command -v wscat &> /dev/null; then
        if timeout 5 wscat -c ws://localhost:8080/ws/live-updates -x &> /dev/null; then
            print_status "WebSocket server health check passed"
        else
            print_warning "WebSocket server health check failed"
        fi
    else
        print_info "wscat not found, skipping WebSocket health check"
    fi

    # Run system health check via API
    if [ "$api_health" = "200" ]; then
        health_response=$(curl -s http://localhost:8000/api/smoke-test/health || echo "{}")
        if echo "$health_response" | grep -q "overall_healthy"; then
            print_status "System health check completed"
        else
            print_warning "System health check returned unexpected response"
        fi
    fi
}

# Initialize system data
initialize_data() {
    print_info "Initializing system data..."

    # Check if initialization scripts exist and run them
    if [ -f scripts/initialize_expert_system.py ]; then
        source venv/bin/activate
        python scripts/initialize_expert_system.py
        print_status "Expert system initialized"
    fi

    # Fetch NFL data if script exists
    if [ -f scripts/fetch_2025_nfl_season.mjs ]; then
        node scripts/fetch_2025_nfl_season.mjs
        print_status "NFL season data fetched"
    fi
}

# Run smoke test
run_smoke_test() {
    print_info "Running smoke test..."

    # Wait for system to be fully ready
    sleep 10

    # Run smoke test via API
    smoke_test_response=$(curl -s -X POST http://localhost:8000/api/smoke-test/run \
        -H "Content-Type: application/json" \
        -d '{"test_games_count": 3, "async_execution": false}' || echo "{}")

    if echo "$smoke_test_response" | grep -q "success"; then
        success=$(echo "$smoke_test_response" | grep -o '"success":[^,]*' | cut -d':' -f2)
        if [ "$success" = "true" ]; then
            print_status "Smoke test passed"
        else
            print_warning "Smoke test failed"
            print_info "Check the test results for details"
        fi
    else
        print_warning "Could not run smoke test"
        print_info "System may still be starting up"
    fi
}

# Display final status
show_final_status() {
    echo ""
    echo "🎉 Quick Start Complete!"
    echo "======================="
    echo ""
    print_info "Your Expert Council Betting System is now running!"
    echo ""
    echo "📊 Service URLs:"
    echo "   • API Server: http://localhost:8000"
    echo "   • WebSocket: ws://localhost:8080"
    echo "   • API Documentation: http://localhost:8000/docs"
    echo ""
    echo "🔍 Health Checks:"
    echo "   • System Health: curl http://localhost:8000/api/smoke-test/health"
    echo "   • API Health: curl http://localhost:8000/health"
    echo "   • Run Smoke Test: curl -X POST http://localhost:8000/api/smoke-test/run"
    echo ""
    echo "📚 Next Steps:"
    echo "   1. Review the deployment guide: docs/deployment_and_startup_guide.md"
    echo "   2. Configure your API keys in .env if not already done"
    echo "   3. Run a comprehensive smoke test"
    echo "   4. Generate your first predictions"
    echo ""
    echo "🛠️ Useful Commands:"
    echo "   • View logs: docker-compose logs -f"
    echo "   • Stop services: docker-compose down"
    echo "   • Restart services: docker-compose restart"
    echo ""
    print_status "System is ready for operation!"
}

# Main execution
main() {
    echo "Starting Expert Council Betting System setup..."
    echo ""

    check_dependencies
    setup_environment
    install_dependencies
    setup_database
    start_services
    run_health_checks
    initialize_data
    run_smoke_test
    show_final_status
}

# Handle script interruption
trap 'print_error "Setup interrupted"; exit 1' INT TERM

# Run main function
main "$@"
