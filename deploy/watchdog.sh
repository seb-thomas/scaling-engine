#!/bin/bash
# Self-healing watchdog. Installed by deploy/install-cron.sh, runs every 5 minutes.
#
# Probes the site through nginx on the server itself and restarts only the
# service that stopped answering. Each run retries a probe 3 times; a service
# is restarted after 3 failed runs in a row (~15 minutes down), and at most
# once per 30 minutes, so a persistent fault can't become a restart loop.
#
# Deliberately NOT a trigger: /api/health/ returning 503. That endpoint reports
# celery / pipeline / cert problems, which restarting web wouldn't fix.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
STATE_DIR="${STATE_DIR:-/var/lib/scaling-engine-watchdog}"
HOST_HEADER="${HOST_HEADER:-radioreads.fun}"
FAIL_THRESHOLD=3
COOLDOWN_SECONDS=1800
DISK_PRUNE_PERCENT=90

mkdir -p "$STATE_DIR"

# Don't fight a deploy or another watchdog run
exec 9>"$STATE_DIR/lock"
flock -n 9 || exit 0

log() { logger -t scaling-engine-watchdog "$*"; echo "$(date -Is) $*"; }

if docker compose version &> /dev/null; then
  DC="docker compose -f $COMPOSE_FILE"
else
  DC="docker-compose -f $COMPOSE_FILE"
fi

# probe <url-path> -> 0 if nginx returns 2xx/3xx, tried 3 times over ~20s
probe() {
  local path="$1" code
  for _ in 1 2 3; do
    # Bypass nginx's page cache, which would otherwise hide a dead frontend
    code=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 -H 'X-Cache-Bypass: 1' \
      --resolve "$HOST_HEADER:443:127.0.0.1" "https://$HOST_HEADER$path")
    [[ "$code" =~ ^[23] ]] && return 0
    sleep 5
  done
  log "probe $path failed (last status $code)"
  return 1
}

# record <service> <ok|fail> -> restarts the service when threshold reached
record() {
  local svc="$1" result="$2" count_file="$STATE_DIR/$1.fails" last_file="$STATE_DIR/$1.last_restart"
  if [ "$result" = ok ]; then
    rm -f "$count_file"
    return
  fi
  local count=$(( $(cat "$count_file" 2>/dev/null || echo 0) + 1 ))
  echo "$count" > "$count_file"
  [ "$count" -lt "$FAIL_THRESHOLD" ] && return

  local now last
  now=$(date +%s)
  last=$(cat "$last_file" 2>/dev/null || echo 0)
  if [ $(( now - last )) -lt "$COOLDOWN_SECONDS" ]; then
    log "$svc still failing after restart; in cooldown, not restarting again"
    return
  fi
  log "restarting $svc after $count consecutive failed checks"
  $DC restart "$svc" && echo "$now" > "$last_file"
  rm -f "$count_file"
}

# Anything stopped (crash loop exhausted, OOM, manual stop) comes back up.
# `up -d` is a no-op for running services.
if [ -n "$($DC ps --status exited -q 2>/dev/null)" ]; then
  log "found exited containers, running up -d"
  $DC up -d
fi

home_ok=ok; api_ok=ok
probe / || home_ok=fail
probe /api/ || api_ok=fail

if [ "$home_ok" = fail ] && [ "$api_ok" = fail ]; then
  # Both behind nginx failing: nginx is the common factor
  record nginx fail
else
  record nginx ok
  record frontend "$home_ok"
  record web "$api_ok"
fi

# Celery reports its own health (inspect ping); a hung worker stops processing
# without exiting, so restart_policy never catches it.
celery_health=$(docker inspect -f '{{.State.Health.Status}}' "$($DC ps -q celery)" 2>/dev/null || echo unknown)
if [ "$celery_health" = unhealthy ]; then
  record celery fail
else
  record celery ok
fi

# Keep the disk from filling with old image layers / build cache
disk_used=$(df --output=pcent / | tail -1 | tr -dc '0-9')
if [ "${disk_used:-0}" -ge "$DISK_PRUNE_PERCENT" ]; then
  log "disk at ${disk_used}%, pruning docker images and build cache"
  docker image prune -af --filter until=72h > /dev/null
  docker builder prune -af > /dev/null
fi

exit 0
