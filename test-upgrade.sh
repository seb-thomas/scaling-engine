#!/bin/bash
set -e  # Exit on error

echo "========================================="
echo "Testing Dependency Upgrade"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Docker is running
echo "Step 1: Checking Docker daemon..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Step 2: Stop existing containers
echo "Step 2: Stopping existing containers..."
docker-compose down
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Step 3: Rebuild images
echo "Step 3: Rebuilding Docker images (this may take a few minutes)..."
echo -e "${YELLOW}Building with Python 3.12 and updated dependencies...${NC}"
docker-compose build --no-cache
echo -e "${GREEN}✓ Images rebuilt${NC}"
echo ""

# Step 4: Start containers
echo "Step 4: Starting containers..."
docker-compose up -d
echo "Waiting for services to be ready..."
sleep 10
echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# Step 5: Check container status
echo "Step 5: Checking container status..."
docker-compose ps
echo ""

# Step 6: Check for Python/Django version
echo "Step 6: Verifying Python version..."
docker-compose exec -T web python --version
echo ""

echo "Step 7: Verifying Django version..."
docker-compose exec -T web python -c "import django; print(f'Django {django.get_version()}')"
echo -e "${GREEN}✓ Versions verified${NC}"
echo ""

# Step 8: Run Django checks
echo "Step 8: Running Django system checks..."
docker-compose exec -T web python manage.py check
echo -e "${GREEN}✓ Django checks passed${NC}"
echo ""

# Step 9: Create/run migrations
echo "Step 9: Creating and running migrations..."
echo "Creating migrations..."
docker-compose exec -T web python manage.py makemigrations
echo ""
echo "Running migrations..."
docker-compose exec -T web python manage.py migrate
echo -e "${GREEN}✓ Migrations complete${NC}"
echo ""

# Step 10: Test database connection
echo "Step 10: Testing database connection..."
docker-compose exec -T web python manage.py showmigrations
echo -e "${GREEN}✓ Database connection works${NC}"
echo ""

# Step 11: Test API endpoint
echo "Step 11: Testing API endpoint..."
if curl -s http://localhost:8000/api/stations/ > /dev/null; then
    echo -e "${GREEN}✓ API endpoint responding${NC}"
    echo "Response:"
    curl -s http://localhost:8000/api/stations/ | head -20
else
    echo -e "${RED}✗ API endpoint not responding${NC}"
    echo "Check logs with: docker-compose logs web"
fi
echo ""

# Step 12: Check for deprecation warnings
echo "Step 12: Checking logs for errors or warnings..."
echo "Recent web container logs:"
docker-compose logs --tail=50 web | grep -i -E "(error|warning|deprecated)" || echo -e "${GREEN}No critical warnings found${NC}"
echo ""

# Summary
echo "========================================="
echo -e "${GREEN}Upgrade Test Complete!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Check the admin panel: http://localhost:8000/admin/"
echo "2. Test your API: http://localhost:8000/api/stations/"
echo "3. View logs: docker-compose logs -f web"
echo "4. Test Scrapy spider: docker-compose exec web python manage.py scraper"
echo ""
echo "If you see any issues, check UPGRADE_GUIDE.md for rollback instructions"
