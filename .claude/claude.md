# Radio Reads - Project Context

## Project Overview
A Django web application that scrapes radio episodes (BBC Radio 4 + NPR), uses AI to extract book mentions, and displays them in a clean NY Times-inspired interface. Supports both HTML scraping (Scrapy, for BBC) and RSS feed parsing (feedparser, for podcast-based shows like NPR Fresh Air).

## Tech Stack
- **Backend**: Django 5.1.4, Django REST Framework
- **Database**: PostgreSQL 16
- **Task Queue**: Celery + Redis
- **Scraping**: Scrapy 2.11.2 (BBC), feedparser (RSS/podcast feeds)
- **AI**: Anthropic Claude API
- **Frontend**: Astro (SSR) + React components, Tailwind CSS
- **Deployment**: Docker Compose, Nginx, Gunicorn

## Frontend Design Principles
- **No loading states**: The frontend is Astro SSR — pages are server-rendered and arrive complete. Do not add loading animations, skeleton screens, spinners, fade-in transitions, or shimmer effects. Content is already there when the page loads.
- **Minimal client-side fetching**: Only fetch on the client for pagination and search. Initial page data comes from SSR props.
- **Typography**: EB Garamond (serif, display) + Inter (sans, body). Use Tailwind `font-serif` class, not inline styles.
- **Hover states**: Use color shifts and underlines, not opacity changes.
- **Tone**: Editorial, minimal, NY Times-inspired. No flashy effects.

## Key Components

### AI Book Extraction (`api/stations/ai_utils.py`)
- Uses Claude API to intelligently detect book mentions in episode descriptions
- Extracts book titles and authors with confidence scoring
- Saves results to database automatically
- Tracks unmatched category suggestions on Book for admin visibility

### Scraping
- **BBC** (`api/scraper/spiders/bbc_episode_spider.py`): Scrapy spider for BBC Radio programme pages. **robots.txt disabled** to access real data. Follows pagination.
- **RSS** (`api/stations/rss_utils.py`): Generic `feedparser`-based scraper for podcast feeds. Works for any brand with `spider_name="rss"` — no new code needed to add another RSS show.
- **Dispatch**: `Brand.spider_name` controls which method is used (`"bbc_episodes"` or `"rss"`).

### Scheduled Tasks (`api/stations/tasks.py`)
- `scrape_all_brands`: Runs daily at 2 AM (dispatches per-brand scrape, staggered)
- `extract_books_from_new_episodes`: Runs every 30 minutes (AI extraction)

### Database Models (`api/stations/models.py`)
- Station → Brand → Episode ↔ Book hierarchy (Episode↔Book is M:N)
- Brand has `spider_name` field for scrape dispatch (`"bbc_episodes"` or `"rss"`)
- Episodes track `has_book` flag and `aired_at` date
- Books store `title`, `author`, and `unmatched_categories` (AI-suggested slugs that don't exist yet)

## Deployment
- **Production**: docker-compose.prod.yml (immutable containers)
- **Development**: docker-compose.dev.yml (volume mounts, hot reload, separate PostgreSQL)
- **URL**: http://159.65.18.16:8080
- **Domain**: radioreads.fun (DNS A record configured, propagating)
- **IP**: 159.65.18.16 (regular IP, not reserved IP)
- **SSL**: Certbot installed, ready to generate certificate once DNS propagates

## Database Setup
- **PostgreSQL 16 required** for both dev and prod (SQLite disabled)
- **Development DB**: `paperwaves_dev` on `localhost:5433`
- **Production DB**: `paperwaves_prod` (internal Docker network)
- **Access production safely**: Use SSH tunnel (see DATABASE.md)
- Django settings enforce PostgreSQL - will fail if misconfigured

## Current Status (Feb 2026)
- ✅ 5 shows live: Front Row, Free Thinking, Bookclub, A Good Read (BBC), Fresh Air (NPR)
- ✅ ~4,500+ episodes scraped across all shows
- ✅ ~295 books extracted with covers, categories, and purchase links
- ✅ RSS scraping for podcast-based shows (generic, reusable)
- ✅ Automated scraping + extraction running daily
- ✅ NY Times-inspired frontend live at radioreads.fun
- ✅ Category admin shows unmatched AI category suggestions

## Todo List

Tracked in Claude memory (`memory/todos.md`). Key open items:
- Historical backfill (BBC shows — code deployed, not yet run at scale)
- WNYC backfill for Fresh Air (full archive back to 2015, needs HTML spider)
- Improve affiliate / support indie bookshops
- Add more shows (NPR Book of the Day, etc.)

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
1. **RSS feed is a rolling window**: NPR Fresh Air RSS has ~300 episodes (~1 year). Full archive (back to 2015) is on WNYC and would need an HTML spider.

## Resolved Issues
- **Google Books cover 403s**: Fixed by rewriting URLs to `/books/publisher/content` in `download_and_save_cover()`.
- **Low book detection rate**: Was 1.8% for Front Row — legitimate, most Front Row episodes cover non-book topics. Shows like Fresh Air and Bookclub have much higher rates.
- **Missing authors**: AI prompt now requires real author name or skips the book.

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
│   │   ├── models.py       # Database models (Brand.spider_name, Book.unmatched_categories)
│   │   ├── views.py        # Views for book listing/detail
│   │   ├── tasks.py        # Celery tasks (spider-agnostic dispatch)
│   │   ├── ai_utils.py     # Claude AI integration + date parsing (BBC + RFC 2822)
│   │   ├── rss_utils.py    # Generic RSS scraper (feedparser)
│   │   └── templates/      # Frontend + admin templates
│   ├── scraper/            # Scrapy project (BBC only)
│   │   ├── spiders/        # BBC episode spider
│   │   └── pipelines.py    # Data processing
│   └── requirements.txt    # Python dependencies
├── frontend/                # Astro SSR + React + Tailwind
├── nginx/                   # Nginx config
├── docker-compose.dev.yml   # Development setup
├── docker-compose.prod.yml  # Production setup
└── .env.prod               # Environment variables
```
