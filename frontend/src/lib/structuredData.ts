// schema.org JSON-LD, so search engines know a page is a book and where it was heard
import type { Book } from '../types'

export const SITE_URL = 'https://radioreads.fun'

export function websiteJsonLd() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'Radio Reads',
    url: `${SITE_URL}/`,
    description: 'Books discussed on BBC Radio 4 and NPR, each with a link to the conversation.',
  }
}

export function bookJsonLd(book: Book, url: string) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Book',
    name: book.title,
    url,
    ...(book.author && { author: { '@type': 'Person', name: book.author } }),
    ...(book.description && { description: book.description }),
    ...(book.cover_image && { image: new URL(book.cover_image, SITE_URL).href }),
    ...(book.topics?.length && { genre: book.topics.map((t) => t.name) }),
    // Each broadcast the book was discussed on
    subjectOf: (book.episodes ?? []).map((ep) => ({
      '@type': 'RadioEpisode',
      name: ep.title,
      ...(ep.url && { url: ep.url }),
      ...(ep.aired_at && { datePublished: ep.aired_at }),
      partOfSeries: {
        '@type': 'RadioSeries',
        name: ep.brand.name,
        url: `${SITE_URL}/show/${ep.brand.slug}`,
        publisher: { '@type': 'Organization', name: ep.brand.station.name },
      },
    })),
  }
}

/** JSON for a <script type="application/ld+json">, safe against a "</script>" in the data */
export function serializeJsonLd(data: object) {
  return JSON.stringify(data).replace(/</g, '\\u003c')
}
