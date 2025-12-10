# Database Management Guide

## Overview

Radio Reads uses **PostgreSQL 16** exclusively for both development and production environments. SQLite is not supported to ensure consistency, predictable migrations, and production-like behavior in development.

## Database Configurations

### Development Database
- **Host**: `localhost:5433` (from host machine) or `db:5432` (from containers)
- **Database**: `paperwaves_dev`
- **User**: `paperwaves_dev_user`
- **Password**: `paperwaves_dev_password`
- **Docker Compose**: `docker-compose.dev.yml`
- **Environment**: `.env.dev` + `.env.dev.db`

### Production Database
- **Host**: `db:5432` (internal to Docker network)
- **Database**: `paperwaves_prod`
- **User**: `paperwaves_user`
- **Password**: See `.env.prod`
- **Docker Compose**: `docker-compose.prod.yml`
- **Environment**: `.env.prod` + `.env.prod.db`

## Common Operations

### Starting Development Environment

```bash
# Start all services (web, db, redis, celery, celery-beat)
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop all services
docker-compose -f docker-compose.dev.yml down
```

### Database Migrations

```bash
# Create new migrations
docker-compose -f docker-compose.dev.yml exec web python manage.py makemigrations

# Apply migrations
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

# Show migration status
docker-compose -f docker-compose.dev.yml exec web python manage.py showmigrations
```

### Accessing Django Shell

```bash
# Development
docker-compose -f docker-compose.dev.yml exec web python manage.py shell

# Production (on server)
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
```

### Creating Superuser

```bash
# Development
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

# Production (on server)
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Connecting to Databases with GUI Clients

### Development Database (Direct Connection)

Use any PostgreSQL client (TablePlus, pgAdmin, DBeaver, psql, etc.):

```
Host: localhost
Port: 5433
Database: paperwaves_dev
User: paperwaves_dev_user
Password: paperwaves_dev_password
```

### Production Database (SSH Tunnel - SAFE Method)

**IMPORTANT**: Never connect development code to the production database. Use SSH tunneling for safe inspection only.

#### Step 1: Create SSH Tunnel

```bash
# Forward production database to local port 5434
ssh -L 5434:localhost:5432 root@159.65.18.16

# Keep this terminal open while you need the connection
```

#### Step 2: Connect via GUI Client

```
Host: localhost
Port: 5434
Database: paperwaves_prod
User: paperwaves_user
Password: e7c3e4096744fe332a40ed8542304325d6c1ab0c
```

#### Step 3: Close Tunnel When Done

Press `Ctrl+C` in the SSH terminal to close the tunnel.

### Using psql Command Line

```bash
# Development (direct)
psql -h localhost -p 5433 -U paperwaves_dev_user -d paperwaves_dev

# Production (via SSH tunnel - run SSH tunnel command first)
psql -h localhost -p 5434 -U paperwaves_user -d paperwaves_prod
```

## Resetting Databases

### Reset Development Database (Safe - No Data Loss)

```bash
# Stop containers
docker-compose -f docker-compose.dev.yml down

# Remove development database volume
docker volume rm scaling-engine_postgres_data_dev

# Start fresh
docker-compose -f docker-compose.dev.yml up -d

# Run migrations
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

### Reset Production Database (DESTRUCTIVE - Use with Caution)

```bash
# On the production server
docker-compose -f docker-compose.prod.yml down

# Remove production database volume
docker volume rm scaling-engine_postgres_data

# Start fresh
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Backup and Restore

### Backup Development Database

```bash
docker-compose -f docker-compose.dev.yml exec db pg_dump -U paperwaves_dev_user paperwaves_dev > backup_dev_$(date +%Y%m%d_%H%M%S).sql
```

### Backup Production Database

```bash
# On production server
docker-compose -f docker-compose.prod.yml exec db pg_dump -U paperwaves_user paperwaves_prod > backup_prod_$(date +%Y%m%d_%H%M%S).sql
```

### Restore from Backup

```bash
# Development
docker-compose -f docker-compose.dev.yml exec -T db psql -U paperwaves_dev_user paperwaves_dev < backup.sql

# Production
docker-compose -f docker-compose.prod.yml exec -T db psql -U paperwaves_user paperwaves_prod < backup.sql
```

## Copying Production Data to Development

```bash
# 1. SSH into production server and create backup
ssh root@159.65.18.16
cd ~/scaling-engine
docker-compose -f docker-compose.prod.yml exec db pg_dump -U paperwaves_user paperwaves_prod > /tmp/prod_backup.sql
exit

# 2. Copy backup to local machine
scp root@159.65.18.16:/tmp/prod_backup.sql ./prod_backup.sql

# 3. Reset development database (see above)
docker-compose -f docker-compose.dev.yml down
docker volume rm scaling-engine_postgres_data_dev
docker-compose -f docker-compose.dev.yml up -d

# 4. Restore production data to development
docker-compose -f docker-compose.dev.yml exec -T db psql -U paperwaves_dev_user paperwaves_dev < prod_backup.sql

# 5. Clean up
rm prod_backup.sql
```

## Troubleshooting

### "Port 5433 already in use"

Another PostgreSQL instance is running on port 5433. Either stop it or change the port in `docker-compose.dev.yml`:

```yaml
db:
  ports:
    - "5434:5432"  # Use different port
```

### "Connection refused" when connecting from host

Make sure the database container is running:

```bash
docker-compose -f docker-compose.dev.yml ps
```

### Migrations out of sync

```bash
# Show migration status
docker-compose -f docker-compose.dev.yml exec web python manage.py showmigrations

# If needed, fake a migration (use with caution)
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate --fake app_name migration_name
```

### "relation does not exist" errors

Run migrations:

```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate
```

## Why PostgreSQL Only?

1. **Consistency**: Same database engine in dev and prod prevents surprises
2. **Predictable Migrations**: PostgreSQL-specific features work everywhere
3. **Feature Parity**: Use advanced PostgreSQL features in development
4. **Debugging**: Behavior matches production exactly
5. **Safety**: Settings enforces PostgreSQL, preventing accidental SQLite usage

## Security Notes

- Development database credentials are simple for local use
- Production database credentials are strong and stored in `.env.prod.db`
- Never commit `.env.prod*` or `.env.dev*` files to git
- Use SSH tunneling (not direct connections) for production database inspection
- Never point development environment at production database
