import type { APIRoute } from 'astro';
import { fetchBooks, fetchShows, fetchTopics } from '../api/client';

const SITE_URL = 'https://radioreads.fun';

export const GET: APIRoute = async () => {
  // Fetch all data for sitemap
  const [allBooks, shows, topics] = await Promise.all([
    fetchAllBooks(),
    fetchShows().catch(() => []),
    fetchTopics().catch(() => []),
  ]);

  const showsList = Array.isArray(shows) ? shows : (shows as any).results || [];
  const topicsList = Array.isArray(topics) ? topics : [];

  const urls: { loc: string; priority: string; changefreq: string }[] = [];

  // Static pages
  urls.push({ loc: '/', priority: '1.0', changefreq: 'daily' });
  urls.push({ loc: '/books', priority: '0.9', changefreq: 'daily' });
  urls.push({ loc: '/shows', priority: '0.8', changefreq: 'weekly' });
  urls.push({ loc: '/topics', priority: '0.8', changefreq: 'weekly' });
  urls.push({ loc: '/about', priority: '0.3', changefreq: 'monthly' });

  // Show pages
  for (const show of showsList) {
    urls.push({ loc: `/show/${show.slug}`, priority: '0.7', changefreq: 'daily' });
  }

  // Topic pages
  for (const topic of topicsList) {
    urls.push({ loc: `/topic/${topic.slug}`, priority: '0.6', changefreq: 'weekly' });
  }

  // Book detail pages
  for (const book of allBooks) {
    const showSlug = book.episodes?.[0]?.brand?.slug;
    if (showSlug) {
      urls.push({ loc: `/${showSlug}/${book.slug}`, priority: '0.7', changefreq: 'monthly' });
    }
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map(u => `  <url>
    <loc>${SITE_URL}${u.loc}</loc>
    <changefreq>${u.changefreq}</changefreq>
    <priority>${u.priority}</priority>
  </url>`).join('\n')}
</urlset>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml' },
  });
};

async function fetchAllBooks() {
  const allBooks: any[] = [];
  let page = 1;
  const pageSize = 100;

  while (true) {
    try {
      const data = await fetchBooks(page, pageSize);
      allBooks.push(...data.results);
      if (!data.next) break;
      page++;
    } catch {
      break;
    }
  }

  return allBooks;
}
