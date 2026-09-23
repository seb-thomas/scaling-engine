# Radio Reads / Scaling Engine

## Mission

This website collects books which have been **discussed or reviewed** on a radio show, or where the **author has been interviewed** about an upcoming book, or otherwise noted (e.g. they've won a notable prize).

**Perfect user**: Someone who listened to the radio yesterday, heard a book being discussed, but missed what it was and wants to find out more. Or someone looking for a gift who knows Radio 4 or Fresh Air is a great source for books.

**We want**: Books that are the _subject_ of the segment - discussed, reviewed, prize-winners, author interviews. Require author + book title (or clear book-type signal: "novel", "book", "short story collection").

**We do NOT want**: Books mentioned only in adaptation context (film, theatre, TV, musical, play) - e.g. "Lord of the Flies adaptation", "A Christmas Carol transformed into hip hop dance", "musical based on Harold Fry". Also exclude TV/film titles mistaken for books (e.g. "thriller Lurker" = TV show).

## Reference

- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) — system design (Episode as single unit of work, scrape → process → extract lifecycle, pipeline).

## Deployment

- **Deploy status**: After a push, use **`gh run watch <run_id>`** (get run ID with `gh run list --repo seb-thomas/scaling-engine --limit 1`). Do not use `sleep` or polling.
- **SSL / Let's Encrypt**: Full procedure is in [DEPLOYMENT.md](DEPLOYMENT.md) (§ SSL / Certificate renewal). Renewal uses webroot; nginx serves `/.well-known/acme-challenge/` from `./certbot-webroot` (gitignored). Cron on the server runs `deploy/renew-cert.sh` twice monthly.
- **Server access**: `ssh radioreads` (host alias in the developer's `~/.ssh/config`, key-based). SSH is key-only — password logins are disabled. If SSH is unreachable, use DigitalOcean's **Recovery Console** (root password); the "Web Console" button goes over SSH and fails with it.
- **One-time server steps** (new server, or expired cert): (1) `mkdir -p /root/scaling-engine/certbot-webroot`, (2) run renewal once (`/root/scaling-engine/deploy/renew-cert.sh`), (3) add the cron entry as in DEPLOYMENT.md.
- **Checking TLS from a work laptop**: a corporate proxy (Netskope) may re-sign HTTPS, so cert checks from the laptop can be misleading. Verify from the server: `openssl s_client -connect 127.0.0.1:443 -servername radioreads.fun`.
- **Monitoring**: UptimeRobot watches the site. `/api/health/` only covers Django — the Astro frontend can be down while it's green, so the homepage needs its own monitor. `.github/workflows/uptime.yml` checks the homepage, `/api/health/` and cert expiry every 30 min from GitHub; a failed run emails.
- **Workflow**: push straight to `master` (no PRs). The deploy runs tests first, then smoke-tests `/` and `/api/` through nginx and fails if either isn't serving.
- **Automation on the server** (`/etc/cron.d/scaling-engine`, written by `deploy/install-cron.sh` on every deploy — edit the script, not the server):
  - `deploy/watchdog.sh` every 5 min: restarts frontend / web / nginx / celery after ~15 min of failed probes, max once per 30 min; prunes Docker when disk ≥ 90%. Log: `/var/log/scaling-engine-watchdog.log`.
  - `deploy/backup-db.sh` nightly 03:30: `pg_dump` to `/root/backups`, 14 days kept (same droplet — restore steps in the script).
  - Weekly Docker image/build-cache prune.
- **Lighthouse** (`.github/workflows/lighthouse.yml`): after every successful deploy and daily at 06:00 UTC, mobile, 3 runs median, on `/`, `/books`, a show page and a book page. Results are run annotations (scores, CWV, failing audits) plus public report links. Budgets in `.github/lighthouse/lighthouserc.json`; an `error` budget failing turns the run red and emails. Scores are Lighthouse's *simulated* throttling — compare `observed*` metrics in the report JSON before concluding a real regression.
- **Flower** is bound to localhost: `ssh -L 5555:localhost:5555 radioreads`, then http://localhost:5555.
