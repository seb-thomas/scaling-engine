#!/bin/bash
# Nightly Postgres backup. Installed by deploy/install-cron.sh.
# Dumps to $BACKUP_DIR (default /root/backups) and keeps $KEEP_DAYS days.
#
# Restore:
#   gunzip -c /root/backups/db-YYYYmmdd-HHMM.sql.gz | \
#     docker compose -f docker-compose.prod.yml exec -T db psql -U paperwaves_user paperwaves_prod
#
# These live on the same droplet, so they cover bad migrations and accidental
# deletes, not losing the server. Enable DigitalOcean droplet backups for that.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
BACKUP_DIR="${BACKUP_DIR:-/root/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"

if docker compose version &> /dev/null; then
  DC="docker compose -f $COMPOSE_FILE"
else
  DC="docker-compose -f $COMPOSE_FILE"
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

target="$BACKUP_DIR/db-$(date +%Y%m%d-%H%M).sql.gz"
tmp="$target.partial"
trap 'rm -f "$tmp"' EXIT

$DC exec -T db pg_dump -U paperwaves_user --no-owner paperwaves_prod | gzip > "$tmp"

# A dump of a live DB is never tiny; an empty file means pg_dump failed quietly
if [ "$(gunzip -c "$tmp" | head -c 4096 | wc -c)" -lt 1024 ]; then
  rm -f "$tmp"
  logger -t scaling-engine-backup "backup FAILED: dump was empty"
  exit 1
fi

mv "$tmp" "$target"
find "$BACKUP_DIR" -name 'db-*.sql.gz' -mtime +"$KEEP_DAYS" -delete
logger -t scaling-engine-backup "backup ok: $target ($(du -h "$target" | cut -f1))"
