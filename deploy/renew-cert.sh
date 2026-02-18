#!/bin/bash
# Let's Encrypt renewal via webroot. Run from project root on the server, or set PROJECT_DIR.
# Cron example: 0 3 1,15 * * /root/scaling-engine/deploy/renew-cert.sh >> /var/log/certbot-renew.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
WEBROOT="${PROJECT_DIR}/certbot-webroot"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.prod.yml"

if [ ! -d "$WEBROOT" ]; then
  echo "Error: webroot not found at $WEBROOT. Create it: mkdir -p $WEBROOT"
  exit 1
fi

if command -v docker-compose &> /dev/null; then
  DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
  DOCKER_COMPOSE="docker compose"
else
  echo "Error: docker-compose not found"
  exit 1
fi

certbot renew --webroot -w "$WEBROOT" \
  --deploy-hook "$DOCKER_COMPOSE -f $COMPOSE_FILE exec -T nginx nginx -s reload"
