#!/bin/bash

# NFL Predictor Development Startup Script
# Starts both frontend and WebSocket server concurrently

echo "🚀 Starting NFL Predictor Development Environment..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check Node version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18 or higher is required. Current version: $(node --version)"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create a .env file with your Supabase credentials."
    echo "   See .env.example for reference."
    exit 1
fi

# Check if Supabase credentials are set
if ! grep -q "VITE_SUPABASE_URL" .env || ! grep -q "VITE_SUPABASE_ANON_KEY" .env; then
    echo "❌ Supabase credentials not found in .env file."
    echo "   Please add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to your .env file."
    exit 1
fi

echo "✅ Environment checks passed"
echo ""

# Kill any existing processes on ports 5173 (Vite) and 8080 (WebSocket)
echo "🧹 Cleaning up any existing processes..."
pkill -f "vite" 2>/dev/null || true
pkill -f "websocketServer.js" 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

echo ""
echo "🌐 Starting services:"
echo "   - Frontend (Vite): http://localhost:5173"
echo "   - WebSocket Server: ws://localhost:8080"
echo ""
echo "📝 Logs will appear below. Press Ctrl+C to stop all services."
echo ""

# Start both services concurrently
npm run dev-full