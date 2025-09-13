#!/bin/bash

# Setup script for secure Python web API

set -e

echo "🚀 Setting up Secure Python Web API..."

# Check if Python 3.8+ is installed
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cp env.example .env
    echo "⚠️ Please edit .env file with your configuration before running the application"
fi

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Check if PostgreSQL is running
echo "🐘 Checking PostgreSQL connection..."
if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "⚠️ PostgreSQL is not running. Please start PostgreSQL before running the application"
    echo "   You can use: sudo systemctl start postgresql"
    echo "   Or use Docker: docker-compose up postgres -d"
fi

# Run database migrations
echo "🗄️ Running database migrations..."
alembic upgrade head

echo "✅ Setup completed successfully!"
echo ""
echo "To start the application:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Edit .env file with your configuration"
echo "3. Start PostgreSQL if not running"
echo "4. Run: python -m app.main"
echo ""
echo "For development with auto-reload:"
echo "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "API documentation will be available at:"
echo "http://localhost:8000/docs"
