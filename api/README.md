# A scraping project

## Considererations:

- Avoid duplicates
- Avoid unnecessary scraping

### Avoid unnecessary scraping

- Pages are scraped, not episodes. How do you avoid scraping unnecessary pages?
- Separate functions for frequency:
- A function to scrape all brand episodes once (full)
- A function just to scrape the latest (daily/partial)
- But if the full scrape job is paused, or restarted.
- ..There is no easy way to avoid unnecessary scraping of pages.

### Avoid duplicates

- Easy: Add all episodes to db, don't check for keywords before saving

  - Function won't save if entry is already there
  - Foreign key to book
  - Filter results to show only those with books.
  - If more keywords are thought of in the future no new scraping needs to be done.

- Harder: Add some episodes to db, process in Scrapy
  - Separate db list with all PIDs of episodes checked for keywords (negative entries)
  - Only add episodes to db,
  - If they have keywords
  - If they have not been checked already
