import type { Book } from '@/types'

export const mockBook: Book = {
  id: 1,
  title: 'Test Book',
  slug: 'test-book',
  author: 'Test Author',
  description: 'A test book description',
  cover_image: 'https://example.com/cover.jpg',
  purchase_link: 'https://example.com/buy',
  episodes: [{
    id: 1,
    title: 'Test Episode',
    slug: 'test-episode',
    url: 'https://example.com/episode',
    aired_at: '2024-01-01T00:00:00Z',
    description: 'Episode description',
    brand: {
      id: 1,
      name: 'Test Show',
      slug: 'test-show',
      station: {
        id: 1,
        name: 'Test Station',
        station_id: 'test',
      },
    },
  }],
} as Book
