#!/bin/bash
# Script to scrape Front Row episodes from host machine
# Requires: Python 3.8+, pip, and database access

set -e

echo "🚀 Scraping Front Row episodes from host machine..."
echo ""

# Check if we're in the right directory
if [ ! -f "api/manage.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
cd api
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if database is accessible
echo "🔍 Checking database connection..."
python manage.py check --database default || {
    echo "❌ Database connection failed. Make sure:"
    echo "   1. Database container is running"
    echo "   2. Database port is exposed (check docker-compose.yml)"
    echo "   3. .env.prod has correct database credentials"
    exit 1
}

# Run the scrape command
echo ""
echo "🎬 Starting scrape..."
python manage.py scrape_front_row

echo ""
echo "✅ Done!"

