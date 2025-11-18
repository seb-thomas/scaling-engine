#!/bin/bash

# DigitalOcean Droplet Deployment Script
# Run this script on your droplet after cloning the repo

set -e

echo "🚀 Starting deployment setup..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (or use sudo)"
    exit 1
fi

# Install Docker and Docker Compose if not already installed
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    apt-get update
    apt-get install -y docker-compose
fi

# Check if .env.prod exists, if not create from example
if [ ! -f .env.prod ]; then
    echo "⚙️  Creating .env.prod from example..."
    cp .env.prod.example .env.prod

    # Generate random secret key
    SECRET_KEY=$(openssl rand -base64 50 | tr -d "=+/" | cut -c1-50)
    sed -i "s/change-me-to-a-secure-random-string/$SECRET_KEY/" .env.prod

    # Generate random db password
    DB_PASSWORD=$(openssl rand -base64 20 | tr -d "=+/" | cut -c1-20)
    sed -i "s/change-me-to-a-secure-password/$DB_PASSWORD/" .env.prod

    echo "⚠️  Please edit .env.prod and set DJANGO_ALLOWED_HOSTS to your domain!"
    echo "   Current value needs to be updated from 'yourdomain.com'"
fi

if [ ! -f .env.prod.db ]; then
    echo "⚙️  Creating .env.prod.db from example..."
    cp .env.prod.db.example .env.prod.db

    # Use the same DB password as .env.prod
    DB_PASSWORD=$(grep SQL_PASSWORD .env.prod | cut -d '=' -f2)
    sed -i "s/change-me-to-a-secure-password/$DB_PASSWORD/" .env.prod.db
fi

# Pull latest code (if this is an update)
if [ -d .git ]; then
    echo "📥 Pulling latest code..."
    git pull
fi

# Build and start containers
echo "🏗️  Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "🚀 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Run migrations
echo "🔄 Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Create superuser if needed (interactive)
echo ""
echo "📝 Do you want to create a Django superuser? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Your app should be running on:"
echo "   http://$(curl -s ifconfig.me):1337"
echo ""
echo "🔍 Check logs with: docker-compose -f docker-compose.prod.yml logs -f"
echo "🛑 Stop with: docker-compose -f docker-compose.prod.yml down"
echo ""
echo "⚠️  IMPORTANT: Update DJANGO_ALLOWED_HOSTS in .env.prod with your domain"
echo "⚠️  IMPORTANT: Set up HTTPS (see DEPLOYMENT.md for instructions)"
