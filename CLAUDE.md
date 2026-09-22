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
- **Monitoring**: UptimeRobot watches the site. `/api/health/` only covers Django — the Astro frontend can be down while it's green, so the homepage needs its own monitor.
