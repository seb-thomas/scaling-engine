# Scraping Front Row Episodes

## Quick Answer: Should I run on host or in Docker?

**For a one-time manual scrape: Host is simpler** ✅
- Easier to see output
- No Docker exec needed
- Better for debugging

**For scheduled/production scraping: Docker is better** ✅
- Already set up with Celery
- Consistent environment
- No manual intervention needed

---

## Option 1: Run on Host Machine (Recommended for One-Time)

### Prerequisites
1. Python 3.8+ installed
2. Database port exposed (see below)
3. Access to `.env.prod` file

### Step 1: Expose Database Port (if not already)

Add this to your `docker-compose.react.yml` under the `db` service:

```yaml
db:
  image: postgres:16-alpine
  ports:
    - "5432:5432"  # Add this line
  # ... rest of config
```

Then restart:
```bash
docker-compose -f docker-compose.react.yml up -d db
```

### Step 2: Set Up Python Environment

```bash
# From project root
python3 -m venv venv
source venv/bin/activate
cd api
pip install -r requirements.txt
```

### Step 3: Configure Database Connection

Make sure your `.env.prod` has:
```bash
SQL_HOST=localhost  # or 127.0.0.1
SQL_PORT=5432
SQL_DATABASE=your_db_name
SQL_USER=your_db_user
SQL_PASSWORD=your_db_password
```

### Step 4: Run Scraper

```bash
cd api
python manage.py scrape_front_row
```

Or use the helper script:
```bash
chmod +x scripts/scrape_front_row_host.sh
./scripts/scrape_front_row_host.sh
```

---

## Option 2: Run in Docker (Simpler Setup)

If you don't want to expose database ports or set up Python on host:

```bash
# Clear mock data and scrape 50 episodes
docker-compose -f docker-compose.react.yml exec web python manage.py scrape_front_row

# Or just scrape (skip clearing)
docker-compose -f docker-compose.react.yml exec web python manage.py scrape_front_row --skip-clear

# Or use scrapy directly
docker-compose -f docker-compose.react.yml exec web scrapy crawl bbc_episodes -a brand_id=1 -a max_episodes=50
```

---

## Option 3: Run via SSH on Remote Server (Recommended for Production)

Perfect for running on your production server without leaving your local machine:

### Method A: One-liner SSH command

```bash
sshpass -pE4wTHGSv5pxY2rs ssh root@159.65.18.16 \
  "cd /root/scaling-engine && docker-compose -f docker-compose.react.yml exec -T web python manage.py scrape_front_row"
```

### Method B: Use the helper script

```bash
# From your local machine
./scripts/ssh_scrape.sh
```

Or manually:
```bash
sshpass -pE4wTHGSv5pxY2rs ssh root@159.65.18.16 'bash -s' < scripts/scrape_front_row_remote.sh
```

### Method C: SSH in and run manually

```bash
# SSH into server
sshpass -pE4wTHGSv5pxY2rs ssh root@159.65.18.16

# Once connected, run:
cd /root/scaling-engine
docker-compose -f docker-compose.react.yml exec web python manage.py scrape_front_row
```

**Benefits:**
- ✅ No need to expose database ports
- ✅ Works directly on production server
- ✅ Can be automated/scripted
- ✅ Uses existing Docker setup

---

## Option 4: Use Existing Celery Task (For Scheduled Scraping)

The scraper is already integrated with Celery. You can trigger it manually:

```bash
# In Django shell
docker-compose -f docker-compose.react.yml exec web python manage.py shell

# Then run:
from stations.tasks import scrape_all_brands
scrape_all_brands.delay()
```

Or modify the task to accept a `max_episodes` parameter.

---

## Troubleshooting

### Database Connection Error
- Check database container is running: `docker-compose ps`
- Verify `.env.prod` credentials match `.env.prod.db`
- If using host, ensure port 5432 is exposed

### Scrapy Errors
- Check BBC website structure hasn't changed
- Verify Front Row brand exists: `python manage.py shell` → `Brand.objects.filter(name__icontains='Front Row')`
- Check network connectivity from container/host

### No Episodes Scraped
- Verify the BBC URL is correct: `https://www.bbc.co.uk/sounds/brand/b006qnlr`
- Check if BBC has changed their HTML structure
- Try accessing the URL manually in a browser

---

## Recommendation

**For your one-time 50-episode scrape on remote server:**
1. Use **Option 3 (SSH)** - easiest and most direct
2. Run: `sshpass -pE4wTHGSv5pxY2rs ssh root@159.65.18.16 "cd /root/scaling-engine && docker-compose -f docker-compose.react.yml exec -T web python manage.py scrape_front_row"`
3. Or use the helper: `./scripts/ssh_scrape.sh`

**For local development:**
- Use **Option 2 (Docker)** - run locally with docker-compose

**For future scheduled scraping:**
- Keep using Celery tasks (already configured)
- They run automatically via `celery-beat` service

