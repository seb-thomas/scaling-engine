"""
System health checks for Radio Reads.

Provides get_system_health() which checks all subsystems and returns
a dict suitable for both the JSON API and the admin dashboard.
"""

import os
import ssl
import socket
import time
import logging
from datetime import datetime, timedelta

from django.db import connection
from django.utils import timezone

logger = logging.getLogger(__name__)

# Simple time-based cache
_cache = {"data": None, "expires": 0}
CACHE_TTL = 30  # seconds


def get_system_health():
    """
    Check all subsystems and return health status dict.

    Cached for 30 seconds to avoid hammering on repeated polls.
    """
    now = time.time()
    if _cache["data"] and now < _cache["expires"]:
        return _cache["data"]

    result = {
        "status": "healthy",
        "checks": {},
        "pipeline": {},
        "timestamp": timezone.now().isoformat(),
    }

    # Run all checks, collect worst status
    _check_database(result)
    _check_redis(result)
    _check_celery_workers(result)
    _check_beat_schedule(result)
    _check_pipeline(result)
    _check_ssl_cert(result)
    _check_api_errors(result)

    # Overall status is worst of all checks
    statuses = [c.get("status") for c in result["checks"].values()]
    if "error" in statuses:
        result["status"] = "unhealthy"
    elif "warning" in statuses:
        result["status"] = "degraded"

    _cache["data"] = result
    _cache["expires"] = now + CACHE_TTL
    return result


def _check_database(result):
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        latency_ms = round((time.time() - start) * 1000)
        result["checks"]["database"] = {
            "status": "ok",
            "latency_ms": latency_ms,
        }
    except Exception as e:
        result["checks"]["database"] = {
            "status": "error",
            "message": str(e)[:200],
        }


def _check_redis(result):
    try:
        import redis

        redis_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
        r = redis.from_url(redis_url, socket_timeout=5)
        start = time.time()
        r.ping()
        latency_ms = round((time.time() - start) * 1000)

        # Check queue depth
        queue_len = r.llen("celery") or 0

        status = "ok"
        message = None
        if queue_len > 50:
            status = "warning"
            message = f"Queue depth: {queue_len}"

        result["checks"]["redis"] = {
            "status": status,
            "latency_ms": latency_ms,
            "queue_depth": queue_len,
        }
        if message:
            result["checks"]["redis"]["message"] = message
    except Exception as e:
        result["checks"]["redis"] = {
            "status": "error",
            "message": str(e)[:200],
        }


def _check_celery_workers(result):
    try:
        from paperwaves.celery import app

        inspect = app.control.inspect(timeout=5.0)
        ping_response = inspect.ping()
        if ping_response:
            worker_names = list(ping_response.keys())
            result["checks"]["celery_workers"] = {
                "status": "ok",
                "workers": len(worker_names),
                "names": worker_names,
            }
        else:
            result["checks"]["celery_workers"] = {
                "status": "error",
                "message": "No workers responding",
                "workers": 0,
            }
    except Exception as e:
        result["checks"]["celery_workers"] = {
            "status": "error",
            "message": str(e)[:200],
            "workers": 0,
        }


def _check_beat_schedule(result):
    try:
        from django_celery_beat.models import PeriodicTask

        extraction_task = PeriodicTask.objects.filter(
            name__icontains="extract_books"
        ).first()
        scrape_task = PeriodicTask.objects.filter(
            name__icontains="scrape_all"
        ).first()

        tasks_info = []
        worst_status = "ok"

        for task_name, task in [("extraction", extraction_task), ("scrape", scrape_task)]:
            if not task:
                tasks_info.append({
                    "name": task_name,
                    "status": "warning",
                    "message": "Task not configured",
                })
                worst_status = "warning"
                continue

            info = {
                "name": task.name,
                "enabled": task.enabled,
                "total_run_count": task.total_run_count,
                "last_run_at": task.last_run_at.isoformat() if task.last_run_at else None,
            }

            if not task.enabled:
                info["status"] = "warning"
                info["message"] = "Disabled"
                worst_status = "warning"
            elif task.last_run_at:
                age = timezone.now() - task.last_run_at
                info["age_minutes"] = round(age.total_seconds() / 60)
                # Extraction runs every 30min, scrape daily — use different thresholds
                stale_minutes = 60 if "extract" in task.name.lower() else 1500  # 25h
                if age.total_seconds() > stale_minutes * 60:
                    info["status"] = "warning"
                    info["message"] = f"Last run {info['age_minutes']}min ago"
                    worst_status = "warning"
                else:
                    info["status"] = "ok"
            else:
                info["status"] = "warning"
                info["message"] = "Never ran"
                worst_status = "warning"

            tasks_info.append(info)

        result["checks"]["beat_schedule"] = {
            "status": worst_status,
            "tasks": tasks_info,
        }
    except Exception as e:
        result["checks"]["beat_schedule"] = {
            "status": "warning",
            "message": str(e)[:200],
        }


def _check_pipeline(result):
    from .models import Episode

    try:
        now = timezone.now()
        last_24h = now - timedelta(hours=24)

        # Counts by status
        awaiting = Episode.objects.filter(status=Episode.STATUS_SCRAPED).count()
        queued = Episode.objects.filter(status=Episode.STATUS_QUEUED).count()
        processing = Episode.objects.filter(status=Episode.STATUS_PROCESSING).count()
        processed_24h = Episode.objects.filter(
            status=Episode.STATUS_PROCESSED,
            processed_at__gte=last_24h,
        ).count()
        failed_24h = Episode.objects.filter(
            status=Episode.STATUS_FAILED,
            status_changed_at__gte=last_24h,
        ).count()
        total = Episode.objects.count()

        # Stuck episodes
        stuck = Episode.stuck(threshold_minutes=60)
        stuck_count = stuck.count()
        stuck_episodes = list(
            stuck.values_list("id", "title", "status", "status_changed_at")[:10]
        )

        # Newest episode
        newest = Episode.objects.order_by("-aired_at").first()
        last_processed = Episode.objects.filter(
            status=Episode.STATUS_PROCESSED
        ).order_by("-processed_at").first()

        # Recent failures
        recent_failures = list(
            Episode.objects.filter(status=Episode.STATUS_FAILED)
            .order_by("-status_changed_at")
            .values_list("id", "title", "last_error", "status_changed_at")[:10]
        )

        status = "ok"
        if stuck_count > 0:
            status = "warning"

        result["checks"]["pipeline"] = {"status": status}
        if stuck_count > 0:
            result["checks"]["pipeline"]["message"] = f"{stuck_count} stuck episode(s)"

        result["pipeline"] = {
            "awaiting_processing": awaiting,
            "queued": queued,
            "processing": processing,
            "processed_24h": processed_24h,
            "failed_24h": failed_24h,
            "total_episodes": total,
            "stuck_count": stuck_count,
            "stuck_episodes": [
                {
                    "id": s[0],
                    "title": s[1][:80],
                    "status": s[2],
                    "status_changed_at": s[3].isoformat() if s[3] else None,
                }
                for s in stuck_episodes
            ],
            "newest_episode": {
                "id": newest.id,
                "title": newest.title[:80],
                "aired_at": newest.aired_at.isoformat() if newest.aired_at else None,
            } if newest else None,
            "last_processed": {
                "id": last_processed.id,
                "title": last_processed.title[:80],
                "processed_at": last_processed.processed_at.isoformat() if last_processed.processed_at else None,
            } if last_processed else None,
            "recent_failures": [
                {
                    "id": f[0],
                    "title": f[1][:80],
                    "error": (f[2] or "")[:200],
                    "failed_at": f[3].isoformat() if f[3] else None,
                }
                for f in recent_failures
            ],
        }
    except Exception as e:
        result["checks"]["pipeline"] = {
            "status": "error",
            "message": str(e)[:200],
        }


def _check_ssl_cert(result):
    """Check SSL certificate expiry for radioreads.fun."""
    try:
        hostname = "radioreads.fun"
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(5)
            s.connect((hostname, 443))
            cert = s.getpeercert()

        not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        days_left = (not_after - datetime.utcnow()).days

        if days_left < 3:
            status = "error"
        elif days_left < 14:
            status = "warning"
        else:
            status = "ok"

        result["checks"]["ssl_cert"] = {
            "status": status,
            "days_left": days_left,
            "expires": not_after.isoformat(),
        }
        if status != "ok":
            result["checks"]["ssl_cert"]["message"] = f"{days_left} days until expiry"
    except Exception as e:
        # SSL check failing is a warning, not error — might be dev environment
        result["checks"]["ssl_cert"] = {
            "status": "warning",
            "message": str(e)[:200],
        }


def _check_api_errors(result):
    """Check for recent API-related failures in the last 24h."""
    from .models import Episode

    try:
        last_24h = timezone.now() - timedelta(hours=24)
        api_errors = Episode.objects.filter(
            status=Episode.STATUS_FAILED,
            status_changed_at__gte=last_24h,
            last_error__icontains="api",
        ).count()

        if api_errors >= 3:
            result["checks"]["external_apis"] = {
                "status": "warning",
                "message": f"{api_errors} API errors in 24h",
                "error_count": api_errors,
            }
        else:
            result["checks"]["external_apis"] = {
                "status": "ok",
                "error_count": api_errors,
            }
    except Exception as e:
        result["checks"]["external_apis"] = {
            "status": "warning",
            "message": str(e)[:200],
        }
