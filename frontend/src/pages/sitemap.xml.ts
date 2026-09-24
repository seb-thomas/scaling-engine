import type { APIRoute } from 'astro';
import { fetchSitemapBooks, fetchShows, fetchTopics } from '../api/client';

const SITE_URL = 'https://radioreads.fun';

export const GET: APIRoute = async () => {
  // Books must load: a sitemap without them would tell search engines
  // those pages are gone, so let a failure error instead
  const [books, shows, topics] = await Promise.all([
    fetchSitemapBooks(),
    fetchShows().catch(() => []),
    fetchTopics().catch(() => []),
  ]);

  const showsList = Array.isArray(shows) ? shows : (shows as any).results || [];
  const topicsList = Array.isArray(topics) ? topics : [];

  const urls: { loc: string; priority: string; changefreq: string; lastmod?: string }[] = [];

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
  for (const book of books) {
    urls.push({
      loc: `/${book.show}/${book.slug}`,
      priority: '0.7',
      changefreq: 'monthly',
      ...(book.lastmod && { lastmod: book.lastmod }),
    });
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls.map(u => `  <url>
    <loc>${SITE_URL}${u.loc}</loc>${u.lastmod ? `
    <lastmod>${u.lastmod}</lastmod>` : ''}
    <changefreq>${u.changefreq}</changefreq>
    <priority>${u.priority}</priority>
  </url>`).join('\n')}
</urlset>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml' },
  });
};
