# Deployment Guide

This guide explains how to deploy the Paperwaves BBC Radio scraping engine to production.

## Architecture Overview

The production stack includes:
- **Nginx**: Reverse proxy and static file serving
- **Django/Gunicorn**: Web application (port 8000)
- **PostgreSQL 16**: Database
- **Redis 7**: Message broker
- **Celery**: Background task processing (episode keyword/AI detection)

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

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check all services are running
docker-compose -f docker-compose.prod.yml ps
```

### 4. Initialize the database

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create a superuser (for Django admin)
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 5. Set up initial data

```bash
# Access Django shell
docker-compose -f docker-compose.prod.yml exec web python manage.py shell

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
docker-compose -f docker-compose.prod.yml exec web scrapy crawl bbc_episodes -a brand_id=1
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
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f web
docker-compose -f docker-compose.prod.yml logs -f celery
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Check Celery worker status

```bash
docker-compose -f docker-compose.prod.yml exec celery celery -A paperwaves inspect active
docker-compose -f docker-compose.prod.yml exec celery celery -A paperwaves inspect stats
```

### Database backups

```bash
# Backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U paperwaves_user paperwaves_prod > backup.sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T db psql -U paperwaves_user paperwaves_prod < backup.sql
```

### Restart services

```bash
# Restart all services
docker-compose -f docker-compose.prod.yml restart

# Restart specific service
docker-compose -f docker-compose.prod.yml restart web
docker-compose -f docker-compose.prod.yml restart celery
```

## Scaling

### Horizontal scaling

To handle more load, scale the web and celery workers:

```bash
# Scale web workers
docker-compose -f docker-compose.prod.yml up -d --scale web=3

# Scale celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery=3
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
docker-compose -f docker-compose.prod.yml logs [service_name]

# Rebuild containers
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### Database connection errors

1. Verify `SQL_PASSWORD` matches `POSTGRES_PASSWORD`
2. Ensure database service is running: `docker-compose -f docker-compose.prod.yml ps db`
3. Check database logs: `docker-compose -f docker-compose.prod.yml logs db`

### Celery tasks not processing

1. Check Redis is running: `docker-compose -f docker-compose.prod.yml ps redis`
2. Verify Celery worker is running: `docker-compose -f docker-compose.prod.yml ps celery`
3. Check Celery logs: `docker-compose -f docker-compose.prod.yml logs celery`

### Static files not loading

```bash
# Recollect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
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

### Option 1: DigitalOcean Droplet
- **Cost**: $12-24/month
- **Pros**: Full control, simple Docker setup
- **Setup**: Use Docker Droplet with 2GB RAM minimum

### Option 2: AWS (EC2 + RDS)
- **Cost**: ~$30-50/month
- **Pros**: Managed database, auto-scaling
- **Setup**: EC2 t3.small + RDS PostgreSQL

### Option 3: Railway.app
- **Cost**: $5-20/month
- **Pros**: Zero-config deployment, built-in CI/CD
- **Setup**: Connect GitHub repo, Railway auto-deploys

### Option 4: Heroku
- **Cost**: $25-50/month
- **Pros**: Managed platform, add-ons for Postgres/Redis
- **Setup**: Use Heroku Postgres and Heroku Redis add-ons

## Support

- **Issues**: https://github.com/seb-thomas/scaling-engine/issues
- **Tests**: All 57 tests passing with 81% coverage
- **Python**: 3.12
- **Django**: 5.1.4 LTS
