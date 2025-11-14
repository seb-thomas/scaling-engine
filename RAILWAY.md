# Railway.app Deployment Guide

Railway doesn't use docker-compose. Instead, you create separate services for each component.

## Step 1: Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will auto-create a database and provide connection variables
4. **Note**: Railway automatically injects these variables into your services:
   - `DATABASE_URL` (we'll need to parse this)

## Step 2: Add Redis

1. Click **"+ New"** again
2. Select **"Database"** → **"Redis"**
3. Railway auto-injects: `REDIS_URL`

## Step 3: Deploy Django Web Service

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your `scaling-engine` repository
3. Railway will auto-detect and deploy using the `Procfile`

### Required Environment Variables

Add these in **Settings → Variables**:

```bash
# Django
SECRET_KEY=your-random-secret-key-here
DEBUG=0
DJANGO_ALLOWED_HOSTS=${{RAILWAY_PUBLIC_DOMAIN}}
PORT=8000

# Database (Railway auto-provides DATABASE_URL, but we need these for Django format)
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=${{PGDATABASE}}
SQL_USER=${{PGUSER}}
SQL_PASSWORD=${{PGPASSWORD}}
SQL_HOST=${{PGHOST}}
SQL_PORT=${{PGPORT}}

# Redis (Railway auto-provides REDIS_URL)
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}

# Book Detection
BOOK_EXTRACTION_MODE=keyword
# ANTHROPIC_API_KEY=your-key  # Optional: Only if using AI mode
```

**Tip**: Railway's `${{VARIABLE}}` syntax references other services automatically.

## Step 4: Deploy Celery Worker Service

1. Click **"+ New"** → **"GitHub Repo"** (same repo again)
2. Select `scaling-engine`
3. In **Settings → Deploy**:
   - Change **Process Type** from `web` to `worker`
4. Add the same environment variables as the web service

## Step 5: Configure Networking

Railway services can communicate using internal URLs:
- PostgreSQL: Automatically connected via `${{PGHOST}}`
- Redis: Automatically connected via `${{REDIS_URL}}`

## Step 6: Deploy!

Railway will automatically deploy when you push to GitHub.

## Troubleshooting

### Build Fails with "No start.sh found"

✅ **Fixed**: We added `Procfile`, `railway.toml`, and `nixpacks.toml`

Push these files:
```bash
git add Procfile railway.toml nixpacks.toml RAILWAY.md
git commit -m "Add Railway deployment configuration"
git push
```

### Database Connection Errors

Railway provides `DATABASE_URL` in format: `postgresql://user:pass@host:port/db`

But Django needs individual variables. Make sure you set:
- `SQL_ENGINE`, `SQL_DATABASE`, `SQL_USER`, etc. using Railway's `${{PG*}}` variables

### Static Files Not Loading

Add this to your web service start command in `Procfile`:
```
web: cd api && python manage.py collectstatic --noinput && python manage.py migrate && gunicorn paperwaves.wsgi:application --bind 0.0.0.0:$PORT
```

Already included in our Procfile! ✅

### Celery Worker Not Processing Tasks

1. Check that the worker service is running (should show "worker" process)
2. Verify `CELERY_BROKER_URL` is set to `${{REDIS_URL}}`
3. Check worker logs for connection errors

## Service Architecture on Railway

```
┌─────────────────────────────────────────────┐
│ Your Railway Project                        │
├─────────────────────────────────────────────┤
│                                             │
│  Service 1: PostgreSQL (Database)           │
│  - Auto-provided by Railway                 │
│  - Variables: PGHOST, PGUSER, PGPASSWORD    │
│                                             │
│  Service 2: Redis (Cache/Broker)            │
│  - Auto-provided by Railway                 │
│  - Variable: REDIS_URL                      │
│                                             │
│  Service 3: Web (Django/Gunicorn)           │
│  - Your GitHub repo                         │
│  - Process: "web" from Procfile             │
│  - Public URL: https://your-app.railway.app │
│                                             │
│  Service 4: Worker (Celery)                 │
│  - Same GitHub repo                         │
│  - Process: "worker" from Procfile          │
│  - No public URL (internal only)            │
│                                             │
└─────────────────────────────────────────────┘
```

## Cost Estimate

- **Hobby Plan**: $5/month (limited to $5 credit)
- **Developer Plan**: ~$15-25/month for this stack
  - Web service: ~$5-10
  - Worker service: ~$5-10
  - PostgreSQL: ~$5
  - Redis: ~$2

Railway charges based on actual resource usage (RAM, CPU, network).

## Scaling

Railway auto-scales resources but not replicas on free tier.

To scale:
- Upgrade to Pro plan ($20/month base)
- Increase replicas in deployment settings
- Horizontal scaling for web and worker services

## Monitoring

Railway provides built-in:
- **Logs**: Real-time logs for all services
- **Metrics**: CPU, RAM, network usage
- **Alerts**: Set up notifications for failures

Access via Railway dashboard → Your service → Metrics/Logs tabs

## Database Backups

Railway Pro includes automatic daily backups for PostgreSQL.

Manual backup:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Backup database
railway run pg_dump > backup.sql
```

## Next Steps

1. ✅ Push Railway config files (done below)
2. ✅ Set up services in Railway dashboard
3. ✅ Add environment variables
4. ✅ Deploy and verify logs
5. Initialize database:
   ```bash
   railway run --service=web python api/manage.py createsuperuser
   ```
6. Add initial data (Station, Brand, Phrases) via Django admin

## Support

- Railway Docs: https://docs.railway.app
- This project: https://github.com/seb-thomas/scaling-engine
- Railway Discord: https://discord.gg/railway
