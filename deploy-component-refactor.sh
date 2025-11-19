#!/bin/bash
# Deploy component refactor to production server

set -e

echo "🚀 Deploying component-based template refactor..."

# Server details
SERVER="root@159.65.18.16"
PROJECT_DIR="~/scaling-engine"
PASSWORD="E4wTHGSv5pxY2rs"

echo "📦 Syncing files to server..."
sshpass -p"$PASSWORD" rsync -avz --progress \
  --exclude='*.pyc' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='*.sqlite3' \
  --exclude='.env*' \
  ./api/stations/templates/ \
  $SERVER:$PROJECT_DIR/api/stations/templates/

sshpass -p"$PASSWORD" rsync -avz --progress \
  ./api/stations/templatetags/ \
  $SERVER:$PROJECT_DIR/api/stations/templatetags/

sshpass -p"$PASSWORD" rsync -avz --progress \
  ./api/stations/static/ \
  $SERVER:$PROJECT_DIR/api/stations/static/

sshpass -p"$PASSWORD" rsync -avz --progress \
  ./api/stations/models.py \
  $SERVER:$PROJECT_DIR/api/stations/models.py

sshpass -p"$PASSWORD" rsync -avz --progress \
  ./api/stations/migrations/ \
  $SERVER:$PROJECT_DIR/api/stations/migrations/

echo "🔄 Running migrations on server..."
sshpass -p"$PASSWORD" ssh $SERVER << 'ENDSSH'
cd ~/scaling-engine

# Run migration
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate

# Restart web container to pick up template changes
docker-compose -f docker-compose.prod.yml restart web

echo "✅ Deployment complete!"
echo "🌐 Visit: http://radioreads.fun"
ENDSSH

echo ""
echo "🎉 Component refactor deployed successfully!"
echo "🌐 Production: http://radioreads.fun"
echo "📊 Check the site to see:"
echo "   - New header with wave logo"
echo "   - Dark mode toggle"
echo "   - Component-based layout"
echo "   - Reusable book cards"
