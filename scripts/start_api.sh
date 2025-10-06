#!/bin/bash
# Start NFL Predictor API Gateway

echo "Starting NFL Predictor API Gateway..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your settings."
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Warning: Redis is not running. Cache will be disabled."
    echo "Start Redis with: redis-server"
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

# Run the API
echo "Starting FastAPI server..."
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload