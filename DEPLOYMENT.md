# Deployment Guide

This guide explains how to deploy the Paperwaves BBC Radio scraping engine to production with React SSR frontend.

## 🚀 Easiest Deployment Method: DigitalOcean Droplet

**Want everything running in 5 minutes with zero configuration?** Use the automated deployment script.

### Why DigitalOcean Droplet?

✅ Deploy with React SSR frontend automatically
✅ No separate database setup - everything runs together
✅ One command deployment
✅ All services included (web, frontend, db, redis, celery, nginx)
✅ Simple and cheap ($6-12/month)

### Quick Start

1. **Create a DigitalOcean Droplet**
   - Go to [DigitalOcean](https://www.digitalocean.com/) → Create Droplet
   - Choose: Ubuntu 22.04 LTS, $12/month plan
   - Copy the IP address

2. **SSH into your Droplet**
   ```bash
   ssh root@your-droplet-ip
   ```

3. **Clone and Deploy**
   ```bash
   git clone https://github.com/seb-thomas/scaling-engine.git
   cd scaling-engine
   chmod +x deploy-to-droplet.sh
   ./deploy-to-droplet.sh
   ```

   The script automatically:
   - Installs Docker & Docker Compose
   - Generates secure random passwords
   - Detects and uses docker-compose.react.yml (includes React frontend)
   - Builds and starts all services (Django API, React SSR frontend, nginx, etc.)
   - Runs database migrations
   - Prompts you to create a superuser

4. **Access Your App**
   - Visit: `http://your-droplet-ip:1337` (React frontend)
   - API: `http://your-droplet-ip:1337/api/`
   - Admin: `http://your-droplet-ip:1337/admin/`

5. **Set Up Your Domain (Optional)**
   - Edit `.env.prod` and update `DJANGO_ALLOWED_HOSTS`
   - Point your domain's A record to the droplet IP
   - Restart: `docker-compose -f docker-compose.react.yml restart`

6. **Enable HTTPS (Recommended)**
   ```bash
   # Install Caddy for automatic HTTPS
   apt install -y caddy

   # Create Caddyfile
   echo "yourdomain.com {
       reverse_proxy localhost:1337
   }" > /etc/caddy/Caddyfile

   # Restart Caddy
   systemctl restart caddy
   ```

That's it! Everything runs from your docker-compose.yml with zero external services.

---

## 📋 Deployment Methods Summary

**For AI tools and developers:** This project supports multiple deployment methods:

1. **Automated Script** (Recommended): `./deploy-to-droplet.sh`
   - Auto-detects `docker-compose.react.yml` (React frontend + Django API)
   - Fallback to `docker-compose.prod.yml` if React config not found
   - Handles all setup automatically

2. **GitHub Actions** (CI/CD): `.github/workflows/deploy.yml`
   - Automatically deploys on push to master
   - Smart detection: uses `docker-compose.react.yml` if available
   - Runs tests before deployment

3. **Manual Deployment**: Use `docker-compose -f docker-compose.react.yml` commands
   - See sections below for specific commands

**Key Files:**
- `docker-compose.react.yml` - Full stack with React SSR frontend (current production)
- `docker-compose.prod.yml` - Legacy Django-only deployment
- `deploy-to-droplet.sh` - Automated deployment script
- `.github/workflows/deploy.yml` - CI/CD pipeline

---

## Architecture Overview

The production stack includes:
- **React SSR Frontend**: Server-side rendered React app (port 3000)
- **Nginx**: Reverse proxy - routes `/` to React, `/api/*` to Django
- **Django/Gunicorn**: REST API backend (port 8000)
- **PostgreSQL 16**: Database
- **Redis 7**: Message broker
- **Celery**: Background task processing (episode keyword/AI detection)

The deployment uses `docker-compose.react.yml` which includes all services.

## Prerequisites

- Docker and Docker Compose installed on your server
- Domain name pointed to your server (optional but recommended)
- Anthropic API key (optional, only for AI book detection)

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/seb-thomas/scaling-engine.git
cd scaling-engine
```

### 2. Create production environment files

```bash
# Copy example files
cp .env.prod.example .env.prod
cp .env.prod.db.example .env.prod.db

# Edit with your actual values
nano .env.prod
nano .env.prod.db
```

**Important settings to change in `.env.prod`:**
- `SECRET_KEY`: Generate a secure random string
- `DJANGO_ALLOWED_HOSTS`: Your domain(s)
- `SQL_PASSWORD`: Choose a strong database password
- `ANTHROPIC_API_KEY`: (Optional) Your Claude API key

**Important settings to change in `.env.prod.db`:**
- `POSTGRES_PASSWORD`: Must match `SQL_PASSWORD` in `.env.prod`

### 3. Build and start production containers

**Note:** The deployment script (`deploy-to-droplet.sh`) automatically uses `docker-compose.react.yml`. For manual deployment:

```bash
# Build images (includes React frontend build)
docker-compose -f docker-compose.react.yml build

# Start services
docker-compose -f docker-compose.react.yml up -d

# Check all services are running
docker-compose -f docker-compose.react.yml ps
```

### 4. Initialize the database

```bash
# Run migrations
docker-compose -f docker-compose.react.yml exec web python manage.py migrate

# Create a superuser (for Django admin)
docker-compose -f docker-compose.react.yml exec web python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.react.yml exec web python manage.py collectstatic --noinput
```

### 5. Set up initial data

```bash
# Access Django shell
docker-compose -f docker-compose.react.yml exec web python manage.py shell

# Create a station and brand
from stations.models import Station, Brand

station = Station.objects.create(
    name="BBC Radio 4",
    station_id="bbc_radio_four",
    url="https://www.bbc.co.uk/programmes/b006qnmr"  # Example: Radio 4
)

brand = Brand.objects.create(
    station=station,
    name="Book Club",  # Example program
    url="https://www.bbc.co.uk/programmes/b006qnmr"
)

# Add keyword phrases for book detection
from stations.models import Phrase
Phrase.objects.create(text="book")
Phrase.objects.create(text="novel")
Phrase.objects.create(text="author")

exit()
```

### 6. Run the scraper

```bash
# Scrape episodes (replace brand_id with your actual brand ID from step 5)
docker-compose -f docker-compose.react.yml exec web scrapy crawl bbc_episodes -a brand_id=1
```

The scraper will:
1. Fetch all episodes from the BBC programme page
2. Save them to the database
3. Trigger Celery tasks to detect book mentions (via keywords or AI)

### 7. Access the application

- **Application**: http://your-server-ip:1337
- **API Endpoint**: http://your-server-ip:1337/api/stations/
- **Django Admin**: http://your-server-ip:1337/admin/

## Configuration Options

### Book Detection Modes

Set `BOOK_EXTRACTION_MODE` in `.env.prod`:

- **`keyword`** (default): Fast regex-based keyword matching
- **`ai`**: Claude AI-powered intelligent extraction (requires `ANTHROPIC_API_KEY`)
- **`both`**: Run both methods for comparison

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DEBUG` | Debug mode (0 for production) | Yes | 0 |
| `SECRET_KEY` | Django secret key | Yes | - |
| `DJANGO_ALLOWED_HOSTS` | Space-separated list of allowed hosts | Yes | - |
| `SQL_DATABASE` | PostgreSQL database name | Yes | - |
| `SQL_USER` | PostgreSQL username | Yes | - |
| `SQL_PASSWORD` | PostgreSQL password | Yes | - |
| `CELERY_BROKER_URL` | Redis broker URL | No | redis://redis:6379/0 |
| `BOOK_EXTRACTION_MODE` | Book detection method | No | keyword |
| `ANTHROPIC_API_KEY` | Claude API key | No (unless mode=ai) | - |

## Monitoring & Maintenance

### View logs

```bash
# All services
docker-compose -f docker-compose.react.yml logs -f

# Specific service
docker-compose -f docker-compose.react.yml logs -f web
docker-compose -f docker-compose.react.yml logs -f frontend
docker-compose -f docker-compose.react.yml logs -f celery
docker-compose -f docker-compose.react.yml logs -f nginx
```

### Check Celery worker status

```bash
docker-compose -f docker-compose.react.yml exec celery celery -A paperwaves inspect active
docker-compose -f docker-compose.react.yml exec celery celery -A paperwaves inspect stats
```

### Database backups

```bash
# Backup
docker-compose -f docker-compose.react.yml exec db pg_dump -U paperwaves_user paperwaves_prod > backup.sql

# Restore
docker-compose -f docker-compose.react.yml exec -T db psql -U paperwaves_user paperwaves_prod < backup.sql
```

### Restart services

```bash
# Restart all services
docker-compose -f docker-compose.react.yml restart

# Restart specific service
docker-compose -f docker-compose.react.yml restart web
docker-compose -f docker-compose.react.yml restart frontend
docker-compose -f docker-compose.react.yml restart celery
```

## Scaling

### Horizontal scaling

To handle more load, scale the web and celery workers:

```bash
# Scale web workers
docker-compose -f docker-compose.react.yml up -d --scale web=3

# Scale celery workers
docker-compose -f docker-compose.react.yml up -d --scale celery=3
```

### Database optimization

For large datasets (100K+ episodes):
1. Add database indexes on frequently queried fields
2. Consider read replicas for PostgreSQL
3. Implement Redis caching for API responses

## Troubleshooting

### Service won't start

```bash
# Check service logs
docker-compose -f docker-compose.react.yml logs [service_name]

# Rebuild containers
docker-compose -f docker-compose.react.yml build --no-cache
docker-compose -f docker-compose.react.yml up -d
```

### Database connection errors

1. Verify `SQL_PASSWORD` matches `POSTGRES_PASSWORD`
2. Ensure database service is running: `docker-compose -f docker-compose.react.yml ps db`
3. Check database logs: `docker-compose -f docker-compose.react.yml logs db`

### Celery tasks not processing

1. Check Redis is running: `docker-compose -f docker-compose.react.yml ps redis`
2. Verify Celery worker is running: `docker-compose -f docker-compose.react.yml ps celery`
3. Check Celery logs: `docker-compose -f docker-compose.react.yml logs celery`

### Frontend not loading

1. Check frontend service is running: `docker-compose -f docker-compose.react.yml ps frontend`
2. Check frontend logs: `docker-compose -f docker-compose.react.yml logs frontend`
3. Verify nginx routing: Check `/etc/nginx/conf.d/nginx.conf` routes `/` to frontend and `/api/` to Django

### Static files not loading

```bash
# Recollect static files
docker-compose -f docker-compose.react.yml exec web python manage.py collectstatic --noinput

# Restart nginx
docker-compose -f docker-compose.react.yml restart nginx
```

## CI/CD with GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:
1. Runs tests on every push and pull request
2. Builds Docker images to verify they compile
3. Runs on PostgreSQL 16 and Redis 7 (matching production)

All commits must pass tests before merging to master.

## Security Best Practices

1. ✅ **Change default passwords**: Never use example passwords in production
2. ✅ **Use HTTPS**: Set up SSL/TLS certificates (use Let's Encrypt)
3. ✅ **Set DEBUG=0**: Never run Django with DEBUG=True in production
4. ✅ **Restrict ALLOWED_HOSTS**: Only allow your actual domain(s)
5. ✅ **Keep dependencies updated**: Run `pip list --outdated` regularly
6. ✅ **Use secrets management**: Consider AWS Secrets Manager or HashiCorp Vault
7. ✅ **Enable database backups**: Automate daily backups
8. ✅ **Monitor logs**: Set up log aggregation (e.g., ELK stack, Datadog)

## Production Hosting Recommendations

### Option 1: DigitalOcean Droplet ⭐ RECOMMENDED
- **Cost**: $12-24/month
- **Pros**: Full control, simple Docker setup, **no external database needed**, everything runs from docker-compose
- **Cons**: You manage the server (minimal effort)
- **Setup**: Use the `deploy-to-droplet.sh` script - 5 minutes to deploy!

### Option 2: AWS (EC2 + RDS)
- **Cost**: ~$30-50/month
- **Pros**: Managed database, auto-scaling
- **Cons**: More expensive, requires separate RDS setup
- **Setup**: EC2 t3.small + RDS PostgreSQL

### Option 3: Railway.app
- **Cost**: $5-20/month
- **Pros**: Zero-config deployment, built-in CI/CD
- **Cons**: Requires separate database setup, doesn't use docker-compose
- **Setup**: Connect GitHub repo, manually configure database

### Option 4: Heroku
- **Cost**: $25-50/month
- **Pros**: Managed platform, add-ons for Postgres/Redis
- **Cons**: Expensive, requires separate add-ons
- **Setup**: Use Heroku Postgres and Heroku Redis add-ons

## Support

- **Issues**: https://github.com/seb-thomas/scaling-engine/issues
- **Tests**: All 57 tests passing with 81% coverage
- **Python**: 3.12
- **Django**: 5.1.4 LTS
