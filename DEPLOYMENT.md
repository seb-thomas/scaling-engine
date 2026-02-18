# Deployment Guide

This guide explains how to deploy the Paperwaves BBC Radio scraping engine to production with React SSR frontend.

## 🚀 Quick Deployment: DigitalOcean + GitHub Actions

**Automatic deployments with zero manual steps.**

**⚠️ IMPORTANT FOR AI ASSISTANTS:** This project uses GitHub Actions for ALL deployments. When changes are pushed to `master`, the workflow automatically:
- Runs tests
- Pulls latest code on the server  
- Rebuilds all Docker containers (including nginx)
- Restarts services with `--force-recreate`

**Never suggest manual rebuilds or restarts** - the CI/CD pipeline handles everything automatically. Just push to master.

**When waiting for deployment to complete:** Use `gh run watch --repo seb-thomas/scaling-engine <run_id>` - **never use `sleep`**. Get the run ID with `gh run list --repo seb-thomas/scaling-engine --limit 1`.

### Why This Setup?

✅ Push to master = automatic deployment
✅ Tests run before every deploy
✅ Full stack: React SSR frontend + Django API
✅ All services included (web, frontend, db, redis, celery, nginx)
✅ Simple and cheap ($6-12/month for droplet)

### One-Time Server Setup

1. **Create a DigitalOcean Droplet**
   - Go to [DigitalOcean](https://www.digitalocean.com/) → Create Droplet
   - Choose: Ubuntu 22.04 LTS, $12/month plan
   - Add your SSH key
   - Copy the IP address

2. **SSH into your Droplet and install Docker**
   ```bash
   ssh root@your-droplet-ip

   # Install Docker & Docker Compose
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   apt-get install -y docker-compose

   # Clone the repo
   git clone https://github.com/seb-thomas/scaling-engine.git
   cd scaling-engine
   ```

3. **Configure GitHub Secrets**

   In your GitHub repository, go to Settings → Secrets → Actions and add:
   - `DO_HOST` - Your droplet IP address
   - `DO_USER` - `root` (or your SSH user)
   - `DO_SSH_KEY` - Your private SSH key
   - `SECRET_KEY` - Generate with `openssl rand -hex 50`
   - `SQL_PASSWORD` - Generate with `openssl rand -hex 20`
   - `ANTHROPIC_API_KEY` - Your Claude API key (optional)

4. **Deploy**
   ```bash
   # From your local machine, just push to master
   git push origin master
   ```

   GitHub Actions will automatically:
   - Run tests
   - SSH into your droplet
   - Build and deploy with `docker-compose.react.yml`
   - Run migrations
   - Start all services

5. **Access Your App**
   - Visit: `https://your-domain.com` (React frontend)
   - API: `https://your-domain.com/api/`
   - Admin: `https://your-domain.com/admin/`

### Future Deployments

Just push to master. That's it. GitHub Actions handles everything.

---

## 📋 Deployment Method

**For AI tools and developers:** This project uses **GitHub Actions for ALL deployments**.

### How to Deploy

**GitHub Actions CI/CD** (`.github/workflows/deploy.yml`)
- ✅ Automatically deploys on push to master
- ✅ Runs tests before deployment
- ✅ Uses `docker-compose.react.yml` (React SSR + Django API)
- ✅ Creates audit trail of all deployments
- ✅ Uses secrets from GitHub (no .env files to manage)

**To deploy:** Just push to master. That's it.

```bash
git add .
git commit -m "Your changes"
git push origin master
# GitHub Actions automatically tests and deploys
```

**Key Files:**
- `docker-compose.react.yml` - Full stack with React SSR frontend (production)
- `.github/workflows/deploy.yml` - CI/CD pipeline (only deployment method)

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

## SSL / Certificate renewal (Let's Encrypt)

The app uses Let's Encrypt certificates. Certs expire after 90 days. Renewal uses **webroot**: nginx serves `/.well-known/acme-challenge/` from a directory where certbot writes challenge files.

**On the server (one-time):**

1. Install certbot: `apt install certbot` (Debian/Ubuntu).
2. Create the webroot directory (same path as in docker-compose):  
   `mkdir -p /root/scaling-engine/certbot-webroot` (or your project path).
3. Renewal command (run manually once to fix an expired cert, or let cron run it):

   ```bash
   certbot renew --webroot -w /root/scaling-engine/certbot-webroot --deploy-hook "docker compose -f /root/scaling-engine/docker-compose.prod.yml exec -T nginx nginx -s reload"
   ```

   Use `docker-compose` instead of `docker compose` if that's what the server has. `--deploy-hook` runs only when a cert was renewed, so nginx reloads only then.

4. **Cron** (run at least twice per 90 days). As root: `crontab -e` and add:

   ```cron
   0 3 1,15 * * certbot renew --webroot -w /root/scaling-engine/certbot-webroot --deploy-hook "docker compose -f /root/scaling-engine/docker-compose.prod.yml exec -T nginx nginx -s reload" >> /var/log/certbot-renew.log 2>&1
   ```

   Or call the script in the repo: `deploy/renew-cert.sh` (see that file for the exact command and path).

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
