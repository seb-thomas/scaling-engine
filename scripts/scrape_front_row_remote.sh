#!/bin/bash
# Script to scrape Front Row episodes on remote server via SSH
# Usage: ssh root@159.65.18.16 'bash -s' < scripts/scrape_front_row_remote.sh
# Or: ssh into server and run: ./scrape_front_row_remote.sh

set -e

echo "🚀 Scraping Front Row episodes on remote server..."
echo ""

# Navigate to project directory (adjust if different)
cd /root/scaling-engine || cd ~/scaling-engine || {
    echo "❌ Error: Could not find scaling-engine directory"
    echo "   Please cd to the project directory first"
    exit 1
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose not found"
    exit 1
fi

# Check if containers are running
if ! docker-compose -f docker-compose.react.yml ps | grep -q "Up"; then
    echo "⚠️  Warning: Docker containers don't appear to be running"
    echo "   Starting containers..."
    docker-compose -f docker-compose.react.yml up -d
    sleep 5
fi

# Run the scraper command
echo "🎬 Running scraper in Docker container..."
echo ""

docker-compose -f docker-compose.react.yml exec -T web python manage.py scrape_front_row

echo ""
echo "✅ Scraping complete!"
echo ""
echo "📊 Checking results..."
docker-compose -f docker-compose.react.yml exec -T web python manage.py shell -c "
from stations.models import Brand, Episode
front_row = Brand.objects.filter(name__icontains='Front Row').first()
if front_row:
    count = Episode.objects.filter(brand=front_row).count()
    print(f'   Front Row episodes in database: {count}')
else:
    print('   Front Row brand not found')
"

