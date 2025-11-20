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

# Check if .env.prod exists, if not create it
if [ ! -f .env.prod ]; then
    echo "⚙️  Creating .env.prod..."

    # Generate random secret key and db password
    SECRET_KEY=$(openssl rand -hex 50)
    DB_PASSWORD=$(openssl rand -hex 20)

    # Get server IP for ALLOWED_HOSTS
    SERVER_IP=$(curl -s ifconfig.me || echo "localhost")

    cat > .env.prod << EOF
# Django Settings
DEBUG=0
SECRET_KEY=$SECRET_KEY
DJANGO_ALLOWED_HOSTS=$SERVER_IP

# Database Settings
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=paperwaves_prod
SQL_USER=paperwaves_user
SQL_PASSWORD=$DB_PASSWORD
SQL_HOST=db
SQL_PORT=5432

# Celery Settings
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379

# AI / Book Extraction
# Options: 'keyword' (legacy), 'ai' (Claude), 'both' (run both methods)
BOOK_EXTRACTION_MODE=keyword
# ANTHROPIC_API_KEY=your-api-key-here  # Only needed if BOOK_EXTRACTION_MODE is 'ai' or 'both'
EOF

    echo "⚠️  .env.prod created with server IP: $SERVER_IP"
    echo "⚠️  You can add a custom domain to DJANGO_ALLOWED_HOSTS later if needed"
fi

if [ ! -f .env.prod.db ]; then
    echo "⚙️  Creating .env.prod.db..."

    # Use the same DB password as .env.prod
    DB_PASSWORD=$(grep SQL_PASSWORD .env.prod | cut -d '=' -f2)

    cat > .env.prod.db << EOF
# PostgreSQL Database Configuration
POSTGRES_USER=paperwaves_user
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=paperwaves_prod
EOF
fi

# Pull latest code (if this is an update)
if [ -d .git ]; then
    echo "📥 Pulling latest code..."
    git pull
fi

# Determine which docker-compose file to use
COMPOSE_FILE="docker-compose.react.yml"
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "⚠️  docker-compose.react.yml not found, using docker-compose.prod.yml"
    COMPOSE_FILE="docker-compose.prod.yml"
fi

# Build and start containers
echo "🏗️  Building Docker images using $COMPOSE_FILE..."
docker-compose -f $COMPOSE_FILE build

echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Run migrations
echo "🔄 Running database migrations..."
docker-compose -f $COMPOSE_FILE exec -T web python manage.py migrate

# Create superuser if needed (interactive)
echo ""
echo "📝 Do you want to create a Django superuser? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    docker-compose -f $COMPOSE_FILE exec web python manage.py createsuperuser
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📍 Your app should be running on:"
echo "   http://$(curl -s ifconfig.me):1337"
echo ""
echo "🔍 Check logs with: docker-compose -f $COMPOSE_FILE logs -f"
echo "🛑 Stop with: docker-compose -f $COMPOSE_FILE down"
echo ""
echo "⚠️  IMPORTANT: Update DJANGO_ALLOWED_HOSTS in .env.prod with your domain"
echo "⚠️  IMPORTANT: Set up HTTPS (see DEPLOYMENT.md for instructions)"
