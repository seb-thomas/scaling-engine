# Database Standardization - Migration Summary

**Date**: December 8, 2025
**Status**: ✅ Complete

## Overview

Successfully standardized the Radio Reads project to use **PostgreSQL exclusively** for both development and production environments, eliminating SQLite fallback behavior and ensuring consistency across all environments.

## Changes Made

### 1. Environment Configuration Files

#### `.env.dev` (Updated)
- Changed database name from `hello_django_dev` to `paperwaves_dev`
- Changed user from `hello_django` to `paperwaves_dev_user`
- Added proper password: `paperwaves_dev_password`
- Added `PAUSE_SCRAPING=True` to disable scheduled tasks in development
- Added comments and better organization

#### `.env.dev.db` (New)
- Created separate PostgreSQL configuration file for development
- Mirrors production pattern with `.env.prod.db`
- Contains: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`

### 2. Docker Compose Configuration

#### `docker-compose.dev.yml` (Created)
- New dedicated development environment configuration
- Uses separate PostgreSQL volume: `postgres_data_dev`
- Exposes database on port `5433` (vs prod on internal `5432`)
- Includes all services: web, db, redis, celery, celery-beat, nginx
- Uses `.env.dev` and `.env.dev.db` for configuration

### 3. Django Settings

#### `api/paperwaves/settings.py` (Updated)
- **Removed SQLite fallback**: No longer defaults to SQLite when env vars missing
- **Added validation**: Enforces PostgreSQL engine requirement
- **Fail-fast behavior**: Raises clear errors if database not properly configured
- **Better error messages**: Tells developers exactly what's missing

**Before:**
```python
"ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
"NAME": os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
```

**After:**
```python
SQL_ENGINE = os.environ.get("SQL_ENGINE")
if not SQL_ENGINE:
    raise ValueError("SQL_ENGINE environment variable is required...")
if SQL_ENGINE != "django.db.backends.postgresql":
    raise ValueError("Only PostgreSQL is supported...")
```

### 4. Version Control

#### `.gitignore` (Updated)
- Added `.env.dev` and `.env.dev.db` to ignore list
- Added `*.sqlite3` and `*.db` patterns
- Added common Python, IDE, OS, and log file patterns
- Ensures no environment files or SQLite databases are committed

### 5. Documentation

#### `DATABASE.md` (New)
Comprehensive guide covering:
- Development vs production database configurations
- Common operations (migrations, shell access, superuser creation)
- GUI client connection instructions (TablePlus, pgAdmin, etc.)
- **Safe production database access via SSH tunnel**
- Database reset procedures
- Backup and restore instructions
- Troubleshooting guide
- Security notes

### 6. Cleanup

- Removed `api/db.sqlite3` (old SQLite database)
- Development environment now starts fresh with PostgreSQL

## Database Configurations

### Development Database
```
Host: localhost:5433 (from host) or db:5432 (from containers)
Database: paperwaves_dev
User: paperwaves_dev_user
Password: paperwaves_dev_password
Volume: postgres_data_dev
```

### Production Database (Unchanged)
```
Host: db:5432 (internal)
Database: paperwaves_prod
User: paperwaves_user
Password: (in .env.prod)
Volume: postgres_data
```

## Key Benefits

1. **Consistency**: Same database engine in dev and prod prevents surprises
2. **Predictable Migrations**: PostgreSQL-specific features work everywhere
3. **Fail-Fast**: Clear errors when misconfigured instead of silently using SQLite
4. **Safety**: Impossible to accidentally point dev at prod database
5. **Debugging**: Easy to inspect dev data with any PostgreSQL client
6. **Documentation**: Clear patterns for database access and operations

## Verification

All services tested and working:
- ✅ PostgreSQL database created and accessible
- ✅ Migrations applied successfully
- ✅ Django settings validate PostgreSQL requirement
- ✅ Database connection verified from containers
- ✅ Port 5433 exposed for direct host access
- ✅ All services start without errors (web, celery, redis)

## How to Use

### Start Development Environment
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Run Migrations
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
```

### Connect with GUI Client
```
Host: localhost
Port: 5433
Database: paperwaves_dev
User: paperwaves_dev_user
Password: paperwaves_dev_password
```

### Access Production Database Safely
```bash
# Create SSH tunnel
ssh -L 5434:localhost:5432 root@159.65.18.16

# Then connect to localhost:5434 with prod credentials
```

## Notes

- **No data loss**: Production database untouched
- **No breaking changes**: Production environment continues using existing setup
- **Development starts fresh**: New PostgreSQL database with no data (by design)
- **Scheduled tasks disabled**: Development won't trigger BBC scraping by default

## Next Steps

1. Developers can populate development database by:
   - Running scraper manually, OR
   - Copying data from production (see DATABASE.md)

2. Update CLAUDE.md with new database approach

3. Consider updating production deployment to use same docker-compose pattern
