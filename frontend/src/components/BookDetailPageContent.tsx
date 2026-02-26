import { useMemo } from 'react'
import { ExternalLink } from 'lucide-react'
import { ImageWithFallback } from './ImageWithFallback'
import { Breadcrumbs } from './Breadcrumbs'
import { Button } from './ui/button'
import { AffiliateDisclosure } from './AffiliateDisclosure'
import { formatDateLong } from '../lib/utils'
import type { Book, BookEpisode } from '../types'

interface BookDetailPageContentProps {
  book: Book
  showSlug?: string
}

function sortEpisodesByAiredAt(episodes: BookEpisode[]): BookEpisode[] {
  return [...episodes].sort((a, b) => {
    const aAt = a.aired_at ? new Date(a.aired_at).getTime() : 0
    const bAt = b.aired_at ? new Date(b.aired_at).getTime() : 0
    return bAt - aAt
  })
}

export function BookDetailPageContent({ book, showSlug }: BookDetailPageContentProps) {
  const sortedEpisodes = useMemo(() => sortEpisodesByAiredAt(book.episodes ?? []), [book.episodes])

  const contextBrand = useMemo(() => {
    if (showSlug && book.episodes?.length) {
      const match = book.episodes.find((ep) => ep.brand.slug === showSlug)
      return match?.brand
    }
    return book.episodes?.[0]?.brand
  }, [showSlug, book.episodes])

  const uniqueBrands = useMemo(() => {
    const seen = new Set<string>()
    return (book.episodes ?? [])
      .map((ep) => ep.brand)
      .filter((b) => {
        if (seen.has(b.slug)) return false
        seen.add(b.slug)
        return true
      })
  }, [book.episodes])

  const breadcrumbItems = uniqueBrands.length > 1
    ? [
        { label: 'Home', href: '/' },
        { label: 'Books', href: '/' },
        { label: book.title }
      ]
    : [
        { label: 'Home', href: '/' },
        ...(contextBrand ? [
          { label: contextBrand.station.name, href: `/station/${contextBrand.station.station_id}` },
          { label: contextBrand.name, href: `/show/${contextBrand.slug}` },
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
                  brandColor={contextBrand?.brand_color}
                />
              </div>
            <div className="flex-1">
              <h1 className="font-serif text-5xl mb-6">
                {book.title}
              </h1>

              {book.author && (
                <div className="text-xl text-gray-600 dark:text-gray-400 mb-4">
                  by {book.author}
                </div>
              )}

              {book.categories && book.categories.length > 0 && (
                <div className="text-xs text-gray-500 dark:text-gray-500 mt-2">
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
          </div>

          <div className="border-y border-gray-200 dark:border-gray-800 py-6">
            <h2 className="text-sm tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-4">
              Featured On
            </h2>
            <div className="space-y-6">
              {sortedEpisodes.map((episode) => (
                <div key={episode.id}>
                  <div className="text-gray-300 dark:text-gray-300 mb-2">
                    <a
                      href={`/show/${episode.brand.slug}`}
                      className="hover:opacity-70 transition-opacity"
                    >
                      {episode.brand.name}, {episode.brand.station.name}
                    </a>
                    {episode.aired_at && (
                      <>
                        <span className="text-gray-500 dark:text-gray-500"> · </span>
                        <span className="text-gray-500 dark:text-gray-500 text-sm">
                          {formatDateLong(episode.aired_at)}
                        </span>
                      </>
                    )}
                  </div>
                  <p className="italic mb-2 text-gray-400 dark:text-gray-400">{episode.title}</p>
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
          </div>

          {book.description && (
            <p className="text-xl leading-relaxed text-gray-400 dark:text-gray-400">
              {book.description}
            </p>
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

