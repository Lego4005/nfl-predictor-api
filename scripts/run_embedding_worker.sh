#!/bin/bash

# Run Embedding Worker with Environment Variables
# This script loads the .env file and runs the embedding worker

echo "🚀 Starting Embedding Worker..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please create a .env file with SUPABASE_URL, SUPABASE_ANON_KEY, and OPENAI_API_KEY"
    exit 1
fi

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Check required environment variables
if [ -z "$VITE_SUPABASE_URL" ] && [ -z "$SUPABASE_URL" ]; then
    echo "❌ Error: SUPABASE_URL or VITE_SUPABASE_URL not found in .env"
    exit 1
fi

if [ -z "$VITE_SUPABASE_ANON_KEY" ] && [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ Error: SUPABASE_ANON_KEY or VITE_SUPABASE_ANON_KEY not found in .env"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY not found in .env"
    exit 1
fi

echo "✅ Environment variables loaded"
echo "📊 Supabase URL: ${VITE_SUPABASE_URL:-$SUPABASE_URL}"
echo "🤖 OpenAI API Key: ${OPENAI_API_KEY:0:20}..."

# Install required packages if not already installed
echo "📦 Checking Python dependencies..."
python3 -c "import supabase, openai" 2>/dev/null || {
    echo "Installing required packages..."
    pip3 install supabase openai
}

# Run the embedding worker
echo "🔄 Starting embedding worker process..."
python3 scripts/embedding_worker.py
