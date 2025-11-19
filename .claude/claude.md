# Radio Reads - Project Context

## Project Overview
A Django web application that scrapes BBC Radio episodes, uses AI to extract book mentions, and displays them in a clean NY Times-inspired interface.

## Tech Stack
- **Backend**: Django 5.1.4, Django REST Framework
- **Database**: PostgreSQL 16
- **Task Queue**: Celery + Redis
- **Scraping**: Scrapy 2.11.2
- **AI**: Anthropic Claude API
- **Frontend**: Django templates with custom CSS
- **Deployment**: Docker Compose, Nginx, Gunicorn

## Key Components

### AI Book Extraction (`api/stations/ai_utils.py`)
- Uses Claude API to intelligently detect book mentions in episode titles
- Extracts book titles and authors with confidence scoring
- Saves results to database automatically

### Scraping (`api/scraper/spiders/bbc_episode_spider.py`)
- Scrapes BBC Radio programme pages for episode listings
- **robots.txt disabled** to access real data
- Follows pagination to get all episodes

### Scheduled Tasks (`api/stations/tasks.py`)
- `scrape_all_brands`: Runs daily at 2 AM (scrapes all BBC shows)
- `extract_books_from_new_episodes`: Runs every 30 minutes (AI extraction)

### Database Models (`api/stations/models.py`)
- Station → Brand → Episode → Book hierarchy
- Episodes track `has_book` flag and `aired_at` date
- Books store `title` and `author`

## Deployment
- **Production**: docker-compose.prod.yml (immutable containers)
- **Development**: docker-compose.dev.yml (volume mounts, hot reload)
- **URL**: http://159.65.18.16:8080
- **Domain**: radioreads.fun (DNS A record configured, propagating)
- **IP**: 159.65.18.16 (regular IP, not reserved IP)
- **SSL**: Certbot installed, ready to generate certificate once DNS propagates

## Current Status (Nov 18, 2025)
- ✅ 3,910 real BBC episodes scraped
- ✅ 82 books extracted from 72 episodes (1.8% detection rate)
- ✅ Automated scraping and extraction working
- ✅ NY Times-inspired frontend live
- ⚠️ Low book detection rate needs investigation

## Todo List

### Completed
- [x] Set up AI book extraction with Anthropic API key
- [x] Redesign frontend with NY Times-inspired aesthetic
- [x] Set up and test radio station scraping
- [x] Fix book saving to database (rebuild containers)
- [x] Create scheduled Celery tasks for automated scraping
- [x] Disable robots.txt to scrape real BBC data

### In Progress
- [ ] Set up HTTPS with Let's Encrypt (waiting for DNS propagation)
  - Certbot installed on host
  - DNS A record configured: radioreads.fun → 159.65.18.16
  - Need to run: `certbot certonly --standalone -d radioreads.fun`
  - Then configure nginx SSL

### Planned
- [ ] Trim down books data (900 is overkill for development) and pause scraping
- [ ] Move static directory to project level (out of stations app)
- [ ] Fix confusing naming - remove /api nesting since there's no separate frontend
- [ ] Investigate why only 1.8% of episodes detected as book-related
- [ ] Add book cover images (API integration or web scraping)
- [ ] Implement AI/web search to find Amazon/book purchase links
- [ ] Set up HTTPS with Let's Encrypt for radioreads.fun
- [ ] Add search and filter functionality for books

## Important Notes

### AI Extraction Mode
- Set via `BOOK_EXTRACTION_MODE` in `.env.prod`
- Options: `ai` (Claude), `keyword` (legacy), `both`
- Currently using: `ai`

### Anthropic API Key
- Stored in `.env.prod`: `ANTHROPIC_API_KEY`
- Used for book extraction via Claude Sonnet

### Robots.txt
- **Disabled** in `api/scraper/settings.py`
- `ROBOTSTXT_OBEY = False`
- Necessary to scrape BBC content

### Database Access
```bash
docker-compose -f docker-compose.dev.yml exec -T web python manage.py shell
```

### Running Scraper Manually
```bash
docker-compose -f docker-compose.dev.yml exec -T web sh -c "scrapy crawl bbc_episodes -a brand_id=2"
```

### Setting up HTTPS (once DNS propagates)
```bash
# Check DNS is working
dig radioreads.fun A +short  # Should show 159.65.18.16

# Stop containers to free port 80
docker-compose -f docker-compose.dev.yml down

# Get SSL certificate
certbot certonly --standalone -d radioreads.fun

# Certificates will be saved to:
# /etc/letsencrypt/live/radioreads.fun/fullchain.pem
# /etc/letsencrypt/live/radioreads.fun/privkey.pem
```

### Trigger AI Extraction
```python
from stations.tasks import extract_books_from_new_episodes
extract_books_from_new_episodes()
```

### Bookshop.org Affiliate Integration
- **Affiliate ID**: 16640
- **Shop Name**: Radio Reads
- **Shop URL**: https://uk.bookshop.org/shop/radioreads
- **Status**: Pending verification (will work once verified)

#### Configuration
- Affiliate ID is configured via `BOOKSHOP_AFFILIATE_ID` environment variable
- Defaults to "16640" if not set
- Add to `.env.prod`: `BOOKSHOP_AFFILIATE_ID=16640`

#### Regenerating Purchase Links
Once affiliate account is verified, regenerate purchase links for existing books:
```bash
docker-compose -f docker-compose.dev.yml exec web python manage.py populate_purchase_links
```

Or with options:
```bash
# Regenerate all links (overwrite existing)
python manage.py populate_purchase_links --overwrite

# Limit to first 100 books
python manage.py populate_purchase_links --limit 100
```

#### How It Works
- New books automatically get Bookshop.org affiliate links when extracted via AI
- Links use format: `https://uk.bookshop.org/search?q={query}&aid=16640`
- Frontend displays "Buy on Bookshop.org" button with required affiliate disclosure
- Disclosure text: "As an affiliate of Bookshop.org, we earn from qualifying purchases. This helps support independent bookstores."

## Known Issues
1. **Low book detection rate**: Only 1.8% of episodes flagged as book-related
   - May need to tune AI prompt or check what titles look like
   - Could be legitimate if Front Row covers many non-book topics

2. **Missing authors**: Many books extracted without author names
   - Episode titles may not always include author information
   - Could enhance AI prompt to infer authors when possible

## Environment Variables

### `.env.prod`
```bash
DEBUG=1
SECRET_KEY=change-me-to-a-secure-random-string
DJANGO_ALLOWED_HOSTS=159.65.18.16,web,localhost
SQL_ENGINE=django.db.backends.postgresql
SQL_DATABASE=paperwaves_prod
SQL_USER=paperwaves_user
SQL_PASSWORD=change-me-to-a-secure-password
SQL_HOST=db
SQL_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379
BOOK_EXTRACTION_MODE=ai
ANTHROPIC_API_KEY=sk-ant-api03-...
BOOKSHOP_AFFILIATE_ID=16640
```

## File Structure
```
/root/scaling-engine/
├── api/
│   ├── paperwaves/          # Django project settings
│   ├── stations/            # Main Django app
│   │   ├── models.py       # Database models
│   │   ├── views.py        # Views for book listing/detail
│   │   ├── tasks.py        # Celery tasks
│   │   ├── ai_utils.py     # Claude AI integration
│   │   └── templates/      # Frontend templates
│   ├── scraper/            # Scrapy project
│   │   ├── spiders/        # BBC episode spider
│   │   └── pipelines.py    # Data processing
│   └── requirements.txt    # Python dependencies
├── nginx/                   # Nginx config
├── docker-compose.dev.yml   # Development setup
├── docker-compose.prod.yml  # Production setup
└── .env.prod               # Environment variables
```
