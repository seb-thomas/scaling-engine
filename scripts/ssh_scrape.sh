#!/bin/bash
# One-liner script to SSH into server and run scraper
# Usage: ./scripts/ssh_scrape.sh

SSH_PASS="${SSH_PASS:-E4wTHGSv5pxY2rs}"
SSH_HOST="${SSH_HOST:-159.65.18.16}"
SSH_USER="${SSH_USER:-root}"

echo "🔐 Connecting to ${SSH_USER}@${SSH_HOST}..."
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "❌ Error: sshpass not found"
    echo "   Install with: brew install hudochenkov/sshpass/sshpass (macOS)"
    echo "   Or: apt-get install sshpass (Linux)"
    exit 1
fi

# Run the remote script
sshpass -p"${SSH_PASS}" ssh -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" 'bash -s' << 'REMOTE_SCRIPT'
set -e

echo "🚀 Scraping Front Row episodes on remote server..."
echo ""

# Navigate to project directory
cd /root/scaling-engine 2>/dev/null || cd ~/scaling-engine 2>/dev/null || {
    echo "❌ Error: Could not find scaling-engine directory"
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
REMOTE_SCRIPT

