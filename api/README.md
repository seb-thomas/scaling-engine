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

### Checking for keywords

- Given the 'easy' route, we need to check for keywords outside of the Scrapy pipeline.
- An episode is saved to the db
- A process runs which checks it for keywords
- Can be on every save, or periodically
  - A function to check for keywords and update with true or false (utils)
  - A task to call the function (tasks)
  - A post save signal added to Scrapy pipeline save
- Will the function
  1. be sent an Episode pk and process?
  2. or iterate over Episode.objects.all()?
- Yes, both
  1. On post save signal.
     - On save
     - Send signal
     - With instance
     - Process single instance
     - Save to db, or pass
  2. Periodic or manual
     - x
