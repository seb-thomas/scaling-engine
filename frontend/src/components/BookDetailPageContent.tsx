import { ExternalLink } from 'lucide-react'
import { ImageWithFallback } from './ImageWithFallback'
import { Breadcrumbs } from './Breadcrumbs'
import { Button } from './ui/button'
import { AffiliateDisclosure } from './AffiliateDisclosure'
import { formatDateLong } from '../lib/utils'
import type { Book } from '../types'

interface BookDetailPageContentProps {
  book: Book
}

export function BookDetailPageContent({ book }: BookDetailPageContentProps) {
  const ep = book.episodes?.[0]
  const brand = ep?.brand

  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    ...(brand ? [
      { label: brand.station.name, href: `/station/${brand.station.station_id}` },
      { label: brand.name, href: `/show/${brand.slug}` },
    ] : []),
    { label: book.title }
  ]

  return (
    <div className="container py-12">
      <Breadcrumbs items={breadcrumbItems} />

      <div className="max-w-3xl">
        <article>
          <div className="flex gap-8 mb-8">
              <div className="flex-shrink-0 w-48" style={{ containerType: 'inline-size' }}>
                <ImageWithFallback
                  src={book.cover_image}
                  alt={`Cover of ${book.title}`}
                  className="w-full h-auto shadow-xl"
                  title={book.title}
                  author={book.author}
                  brandColor={brand?.brand_color}
                />
              </div>
            <div className="flex-1">
              {brand && (
                <div className="text-xs tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-4">
                  {brand.name}
                </div>
              )}

              <h1 className="font-serif text-5xl mb-6">
                {book.title}
              </h1>

              {book.author && (
                <div className="text-xl text-gray-600 dark:text-gray-400 mb-8">
                  by {book.author}
                </div>
              )}
            </div>
          </div>

          <div className="border-y border-gray-200 dark:border-gray-800 py-6 mb-8">
            <h2 className="text-sm tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-3">
              Featured On
            </h2>
            {book.episodes.map((episode) => (
              <div key={episode.id} className="mb-2">
                <a
                  href={`/show/${episode.brand.slug}`}
                  className="hover:opacity-70 transition-opacity"
                >
                  {episode.brand.name}, {episode.brand.station.name}
                </a>
                {episode.aired_at && (
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {' · '}{formatDateLong(episode.aired_at)}
                  </span>
                )}
              </div>
            ))}
            {book.categories && book.categories.length > 0 && (
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-3">
                {book.categories.map((c, i) => (
                  <span key={c.slug}>
                    {i > 0 && ' · '}
                    <a
                      href={`/topic/${c.slug}`}
                      className="hover:text-[#c1573a] dark:hover:text-[#c1573a] transition-colors"
                    >
                      {c.name}
                    </a>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="mb-8">
            <h2 className="text-sm tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-3">
              {book.episodes.length > 1 ? 'Episodes' : 'Episode'}
            </h2>
            {book.episodes.map((episode) => (
              <div key={episode.id} className="mb-4">
                <p className="italic mb-1">{episode.title}</p>
                {episode.aired_at && (
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                    {formatDateLong(episode.aired_at)}
                  </div>
                )}
                {episode.url && (
                  <a
                    href={episode.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors underline"
                  >
                    Listen to episode
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            ))}
          </div>

          {book.description && (
            <div className="mb-8">
              <p className="text-xl leading-relaxed text-gray-700 dark:text-gray-300">
                {book.description}
              </p>
            </div>
          )}

          {book.purchase_link && (
            <div className="bg-gray-100 dark:bg-gray-900 p-6 rounded">
              <p className="text-sm text-gray-700 dark:text-gray-300 mb-4">
                Interested in reading this book?
              </p>
              <Button variant="outline" asChild>
                <a
                  href={book.purchase_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2"
                >
                  Buy on Bookshop.org
                  <ExternalLink className="w-4 h-4" />
                </a>
              </Button>
              <AffiliateDisclosure />
            </div>
          )}
        </article>
      </div>
    </div>
  )
}

