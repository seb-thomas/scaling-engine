# System architecture (merged design)

This document describes the current system design after merging **RawEpisodeData** into **Episode**: Episode is the single unit of work (snapshot + processing state + output). Scraping, extraction, and admin all operate on Episode.

## Truths / guarantees

- **Scrape source**: The system knows what to scrape from `Brand.url` (BBC show page listing).
- **Discovery**: Episodes are discovered from the listing HTML on each run.
- **Immutability**: An episode is scraped once and never refreshed; BBC descriptions are immutable.
- **Idempotency**: `Episode.url` is unique at DB level; the spider skips when `Episode.objects.filter(url=...).exists()`, so duplicate URLs are never stored.
- **Single unit of work**: Episode holds the scraped snapshot, pipeline status, and derived output (books). There is no separate raw-data table.
- **Reprocessing**: Reprocessing an episode regenerates derived Books deterministically via **replace semantics** (delete all books for the episode, then create new ones from the latest extraction).

## Lifecycle

1. **Scrape**
   - Start from each Brand URL; spider discovers episode URLs from the listing.
   - For each **new** URL: create an Episode (brand, title, url; slug auto), store the full payload in `Episode.scraped_data`, set `Episode.status = SCRAPED`.
   - For existing URLs: do nothing (skip).

2. **Process (scheduled)**
   - Select episodes where `Episode.status == SCRAPED` (e.g. up to 50 per run).
   - Before enqueueing: set `Episode.status = QUEUED`, clear `last_error` (and optionally `processed_at`).
   - Enqueue `ai_extract_books_task.delay(episode.id)`.

3. **Extract + apply**
   - Task sets `Episode.status = PROCESSING`, `task_id = celery_task_id`, `last_error = None`.
   - Read description from `Episode.scraped_data` (title + description); call Claude; parse JSON.
   - Store `Episode.extraction_result` (debug/admin).
   - **Replace books**: `Book.objects.filter(episode=episode).delete()`, then create new Book rows from the extraction.
   - Update `Episode.has_book` and, if missing, `Episode.aired_at` from `scraped_data["date_text"]`.
   - Set `Episode.status = PROCESSED`, `Episode.processed_at = now()`, clear `last_error`. On failure: `Episode.status = FAILED`, `Episode.last_error = "<short message>"`.

4. **Operate**
   - Django admin Episode page is the operational cockpit: status chip, scraped description preview, extraction reasoning preview, list of Books, and “Reprocess (AI)” (single and bulk). Optional Flower link when `FLOWER_URL` is set.

## Domain models (merged)

- **Station** → **Brand** (1:N): Brand has `url` = BBC brand/show page.
- **Brand** → **Episode** (1:N): Episode has `url` (unique), `title`, `slug`, `aired_at`, `has_book`, plus:
  - **Snapshot**: `scraped_data` (JSON: url, title, date_text, description, meta_tags, html_title, etc.)
  - **Pipeline**: `status` (SCRAPED | QUEUED | PROCESSING | PROCESSED | FAILED), `processed_at`, `last_error`, `task_id`, `extraction_result`
- **Episode** → **Book** (1:N): Books are derived from extraction; reprocess replaces all books for that episode.

Station, Brand, and Phrase are configuration/content; Episode and Book are the scraped and derived data.

## Architecture diagram (full)

```mermaid
flowchart TB
  subgraph host [Host]
    systemd[systemd scaling-engine.service]
    cron[cron certbot renew]
  end

  subgraph health [Health]
    APIHealth["GET /api/health/ DB + Redis"]
    DockerHC[Docker healthchecks web db redis celery beat]
  end

  subgraph external [External]
    BBC[BBC Sounds]
    Claude[Claude API]
  end

  subgraph config [Configuration]
    Station[(Station)]
    Brand[(Brand url = BBC brand page)]
    Station -->|1:N| Brand
  end

  subgraph scraping [Scraping discovery + snapshot]
    Spider[Scrapy Spider BbcEpisodeSpider]
    Pipeline[SaveToDbPipeline]
    Brand -->|start url| Spider
    BBC --> Spider
    Spider -->|discover episode urls skip if exists| Pipeline
    Spider -->|follow new episode urls to detail| Pipeline
  end

  subgraph django [Django serve + operate]
    Nginx[Nginx]
    Web[Django Gunicorn]
    Frontend[React SSR]
    API[REST API]
    Admin[Django Admin]
    Nginx --> Web
    Nginx --> Frontend
    Web --> API
  end

  subgraph models [Domain models merged]
    Episode[(Episode brand title url slug scraped_data status processed_at last_error task_id extraction_result aired_at has_book)]
    Book[(Book episode-scoped)]
    Brand -->|1:N| Episode
    Episode -->|1:N| Book
  end

  subgraph storage [Storage]
    DB[(PostgreSQL)]
    Redis[(Redis broker + results)]
  end

  subgraph celery [Celery]
    Beat[Celery Beat]
    Worker[Celery Worker]
    ScrapeTask[scrape_all_brands daily]
    DetectTask["extract_books_from_new_episodes 30min select SCRAPED set QUEUED"]
    AITask[ai_extract_books_task]
    Beat --> ScrapeTask
    Beat --> DetectTask
    ScrapeTask --> Worker
    DetectTask --> Worker
    Worker --> AITask
  end

  subgraph extraction [Extraction replace semantics]
    ReadSnap["read Episode.scraped_data.description"]
    CallAI["call Claude + parse"]
    SaveResult["write Episode.extraction_result"]
    ReplaceBooks["delete Book rows create new Book rows"]
    UpdateEpisode["set has_book set aired_at if empty"]
    SetStatus["status PROCESSED or FAILED processed_at last_error"]
    AITask --> ReadSnap --> CallAI --> SaveResult --> ReplaceBooks --> UpdateEpisode --> SetStatus
    CallAI --> Claude
  end

  subgraph monitoring [Monitoring optional]
    Flower[Flower]
    Flower --> Redis
  end

  Pipeline --> Episode
  models --> DB
  Worker --> Redis
  Admin -->|"Episode admin status + reprocess enqueues AITask"| AITask
  Web -->|healthcheck| APIHealth
  DockerHC --> Web
  DockerHC --> DB
  DockerHC --> Redis
  DockerHC --> Worker
  DockerHC --> Beat
  systemd -->|starts| Nginx
  cron -->|reload nginx after renew| Nginx
```

## Pipeline flow (high level)

```mermaid
flowchart LR
  subgraph scrape [Scraping]
    Spider[BbcEpisodeSpider]
    Pipeline[SaveToDbPipeline]
    Spider -->|new URL only| Pipeline
    Pipeline -->|scraped_data status=SCRAPED| Episode[Episode]
  end
  subgraph process [Processing]
    Scheduler[extract_books_from_new_episodes]
    AITask[ai_extract_books_task]
    Scheduler -->|status=SCRAPED to QUEUED| AITask
    AITask -->|PROCESSING then PROCESSED or FAILED| Episode
  end
  Episode -->|1:N| Book[Book]
```

- **Scraping**: Spider discovers episode URLs from Brand page; for new URLs, pipeline creates Episode and sets `scraped_data` and `status=SCRAPED`.
- **Scheduler**: Picks `status=SCRAPED`, sets `QUEUED`, enqueues `ai_extract_books_task`.
- **Extraction**: Task sets `PROCESSING`; reads from `scraped_data`; calls Claude; replaces Books; sets `PROCESSED` or `FAILED` and timestamps/errors on Episode.

## Celery tasks

| Task | Schedule / trigger | Role |
|------|--------------------|------|
| `scrape_all_brands` | Celery Beat (e.g. daily) | Runs Scrapy for each Brand; new episodes get `scraped_data` and `status=SCRAPED`. |
| `extract_books_from_new_episodes` | Celery Beat (e.g. every 30 min) | Selects `Episode.status=SCRAPED`, sets `QUEUED`, enqueues `ai_extract_books_task` per episode. |
| `ai_extract_books_task(episode_id)` | Enqueued by scheduler or admin reprocess | Sets `PROCESSING`, runs extraction, replaces Books, sets `PROCESSED` or `FAILED`. |

## API safety

Public REST API **must not** expose pipeline/debug fields. Episode serializer uses explicit `fields` and **excludes** `scraped_data`, `extraction_result`, `last_error`, `task_id`. Those are for admin and debugging only.

## Key files

| Area | File | Purpose |
|------|------|---------|
| Models | `api/stations/models.py` | Episode (with scraped_data, status, extraction_result, etc.), Book, Brand, Station. |
| Scraping | `api/scraper/pipelines.py` | SaveToDbPipeline: writes `scraped_data` and `status=SCRAPED` to Episode. |
| Scraping | `api/scraper/spiders/bbc_episode_spider.py` | Discovers episode URLs from Brand page; fills `_raw_data_cache` for pipeline. |
| Tasks | `api/stations/tasks.py` | Status transitions; selector by `status=SCRAPED`; enqueue with `QUEUED`. |
| Extraction | `api/stations/ai_utils.py` | Reads `scraped_data`; replace Books; sets `extraction_result`, `PROCESSED`/`FAILED`. |
| Admin | `api/stations/admin.py` | Episode list/change: status, previews, reprocess single/bulk; extraction evaluation view. |
| Config | `api/paperwaves/settings.py` | `FLOWER_URL` (optional) for admin “Open Flower” link. |

## Data wipe (migrations)

The merge was done with **drop all data**: no backfill from RawEpisodeData. Migrations add the new Episode fields, then truncate Book and Episode (and the old RawEpisodeData table) and remove the RawEpisodeData model. Station/Brand/Phrase are kept so scraping can run against existing brands. After migrations, Episode and Book tables start empty.
