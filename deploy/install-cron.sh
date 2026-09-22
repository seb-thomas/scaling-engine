#!/bin/bash
# Installs the server's scheduled jobs into /etc/cron.d/scaling-engine.
# Idempotent: the deploy workflow runs it on every deploy, so edits to this
# file reach the server with the next push to master.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CRON_FILE=/etc/cron.d/scaling-engine

if [ ! -w /etc/cron.d ]; then
  echo "install-cron: /etc/cron.d not writable (not root?), skipping"
  exit 0
fi

chmod +x "$SCRIPT_DIR/watchdog.sh" "$SCRIPT_DIR/backup-db.sh" "$SCRIPT_DIR/renew-cert.sh"

cat > "$CRON_FILE.tmp" <<EOF
# Managed by deploy/install-cron.sh in the scaling-engine repo. Do not edit here.
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Self-healing: restart services that stop answering
*/5 * * * * root $SCRIPT_DIR/watchdog.sh >> /var/log/scaling-engine-watchdog.log 2>&1

# Nightly database backup, 14 days kept in /root/backups
30 3 * * * root $SCRIPT_DIR/backup-db.sh >> /var/log/scaling-engine-backup.log 2>&1

# Weekly: drop unused images and build cache (each deploy builds on the server)
0 4 * * 0 root docker image prune -af --filter until=168h > /dev/null && docker builder prune -af --filter until=168h > /dev/null

# Keep our own logs small
0 5 * * 0 root for f in /var/log/scaling-engine-*.log; do tail -n 2000 "\$f" > "\$f.tmp" && mv "\$f.tmp" "\$f"; done
EOF

chmod 644 "$CRON_FILE.tmp"
mv "$CRON_FILE.tmp" "$CRON_FILE"
echo "install-cron: installed $CRON_FILE (project $PROJECT_DIR)"
