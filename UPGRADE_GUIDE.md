# Upgrade Guide: 2020 → 2025

This document outlines the major dependency upgrades and changes made to modernize the codebase.

## Summary of Changes

### Dependency Upgrades

| Package | Old Version | New Version | Notes |
|---------|-------------|-------------|-------|
| **Django** | 3.1b1 (beta!) | 5.1.4 (LTS) | Major version jump, LTS support until 2026 |
| **Python** | 3.8.3 | 3.12 | End-of-life → Current stable |
| **Celery** | 4.4.6 | 5.4.0 | Major version upgrade |
| **Scrapy** | 2.2.0 | 2.11.2 | Minor breaking changes |
| **DRF** | 3.11.0 | 3.15.2 | Backward compatible |
| **cryptography** | 2.9.2 | 43.0.3 | CRITICAL security fixes |
| **Twisted** | 20.3.0 | 24.11.0 | Multiple CVEs fixed |
| **lxml** | 4.5.1 | 5.3.0 | Security & performance |
| **redis** | 3.5.3 | 5.2.1 | Major version upgrade |
| **gunicorn** | 20.0.4 | 23.0.0 | Security & stability |

### Code Changes Made

#### 1. Django Settings (`api/paperwaves/settings.py`)
- ✅ Added `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"` (required for Django 3.2+)
- ✅ Updated CORS settings: `CORS_ORIGIN_WHITELIST` → `CORS_ALLOWED_ORIGINS` (django-cors-headers 4.x)
- ✅ Fixed `DEBUG` variable duplication
- ✅ Added default value for `DJANGO_ALLOWED_HOSTS` environment variable

#### 2. Dockerfiles
- ✅ Updated `api/Dockerfile`: Python 3.8.3 → 3.12
- ✅ Updated `api/Dockerfile.prod`: Python 3.8.3 → 3.12 (both stages)

#### 3. Bug Fixes (already applied)
- ✅ Fixed `Brand.objects.first()` in spider
- ✅ Fixed `Phrase().keyword_list` inefficiency
- ✅ Added proper exception handling in Scrapy pipeline
- ✅ Added Celery task retry logic

### Backup Created
- 📁 `api/requirements.txt.backup` - Contains original dependencies

---

## Migration Steps

### 1. Rebuild Docker Containers

```bash
# Stop existing containers
docker-compose down

# Remove old images to force rebuild
docker-compose build --no-cache

# Start fresh containers
docker-compose up -d
```

### 2. Run Django Migrations

Django 5.1 may generate new migrations for `DEFAULT_AUTO_FIELD`:

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

**Expected output:** Migrations for changing AutoField → BigAutoField

### 3. Test Core Functionality

#### a) Admin Panel
```bash
# Visit http://localhost:8000/admin/
# Should load without errors
```

#### b) API Endpoints
```bash
# Test stations API
curl http://localhost:8000/api/stations/
```

#### c) Celery Worker
```bash
# Check Celery is running
docker-compose logs web | grep -i celery

# Should see: "celery@hostname ready"
```

#### d) Run Scrapy Spider
```bash
docker-compose exec web python manage.py scraper
```

### 4. Check for Deprecation Warnings

```bash
# Run Django checks
docker-compose exec web python manage.py check

# Should show: System check identified no issues
```

---

## Breaking Changes to Watch For

### Django 3.1 → 5.1

✅ **Already Handled:**
- `DEFAULT_AUTO_FIELD` setting added
- CORS settings updated
- Already using `path()` instead of deprecated `url()`

⚠️ **Potential Issues:**
- If you have custom middleware, check order (unlikely)
- If using `django.contrib.postgres` fields, syntax may have changed slightly

### Celery 4 → 5

✅ **Already Handled:**
- Task retry configuration updated
- Import paths still work (backward compatible)

⚠️ **Potential Issues:**
- If you add new Celery config, use new `task_*` prefix instead of `CELERY_*`
- Celery beat schedule format changed slightly (if you use scheduled tasks)

### Scrapy 2.2 → 2.11

✅ **Should be compatible** - mostly bug fixes and improvements

⚠️ **Monitor:**
- CSS selectors may behave slightly differently
- Check spider output for parsing errors

---

## Rolling Back (If Needed)

If you encounter critical issues:

```bash
# Stop containers
docker-compose down

# Restore old requirements
cp api/requirements.txt.backup api/requirements.txt

# Revert settings changes (manual)
git diff api/paperwaves/settings.py

# Revert Dockerfiles
git checkout api/Dockerfile api/Dockerfile.prod

# Rebuild with old versions
docker-compose build --no-cache
docker-compose up -d
```

---

## Security Improvements

The upgrade fixes multiple **critical vulnerabilities**:

### High Priority CVEs Fixed
- **Django**: 15+ security fixes (XSS, SQL injection, CSRF)
- **cryptography**: OpenSSL vulnerabilities
- **Twisted**: Remote code execution vulnerabilities
- **lxml**: XML parsing vulnerabilities
- **Pillow**: Image processing vulnerabilities (if used)

### Recommendations
1. ⚠️ Change `SECRET_KEY` in production (if same as dev)
2. ⚠️ Set `DEBUG=0` in production
3. ⚠️ Use proper `ALLOWED_HOSTS` (not `*`)
4. ⚠️ Enable HTTPS in production (update CORS settings)

---

## Next Steps (Optional)

### 1. Add Testing Infrastructure
```bash
pip install pytest pytest-django pytest-cov
```

### 2. Add Development Tools
```bash
pip install black ruff mypy django-debug-toolbar
```

### 3. Add Monitoring
```bash
pip install flower  # Celery monitoring
pip install django-extensions  # Django utilities
```

### 4. Consider Adding
- **Sentry** for error tracking
- **django-environ** for better env management
- **django-health-check** for monitoring
- **API documentation** (drf-spectacular)

---

## Verification Checklist

After migration, verify:

- [ ] Admin panel loads (`/admin/`)
- [ ] API returns data (`/api/stations/`)
- [ ] Scrapy spider runs without errors
- [ ] Celery tasks process successfully
- [ ] Database connections work
- [ ] Redis connections work
- [ ] Docker containers stay running
- [ ] No Python/Django deprecation warnings
- [ ] Logs show no errors

---

## Support

If you encounter issues:

1. Check Django 5.1 release notes: https://docs.djangoproject.com/en/5.1/releases/
2. Check Celery 5.x migration guide: https://docs.celeryproject.org/en/stable/whatsnew-5.0.html
3. Check container logs: `docker-compose logs -f web`

---

## Version History

- **2025-01-14**: Major dependency upgrade (2020 → 2025 versions)
- **2020-05**: Initial project creation
