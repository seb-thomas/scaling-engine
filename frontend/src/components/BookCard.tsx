import { ImageWithFallback } from './ImageWithFallback'
import { formatDateLong, formatDateShort } from '@/lib/utils'
import type { Book } from '@/types'

/** Truncate text at word boundary, max length chars */
function truncateAtWord(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  const truncated = text.slice(0, maxLength)
  const lastSpace = truncated.lastIndexOf(' ')
  // If no space found or it's too early, just use the truncated version
  if (lastSpace < maxLength * 0.5) return truncated.trim() + '…'
  return truncated.slice(0, lastSpace).trim() + '…'
}

type BookCardProps = {
  book: Book
  featured?: boolean
}

export function BookCard({ book, featured = false }: BookCardProps) {
  if (featured) {
    return (
      <a
        href={`/${book.episode.brand.slug}/${book.slug}`}
        className="group block"
      >
        <article className="border-b border-gray-200 dark:border-gray-800 pb-8 mb-8">
          <div className="flex gap-6 mb-6">
            {book.cover_image && (
              <div className="flex-shrink-0 w-32">
                <ImageWithFallback
                  src={book.cover_image}
                  alt={`Cover of ${book.title}`}
                  className="w-full h-auto shadow-lg"
                />
              </div>
            )}
            <div className="flex-1">
              <div className="text-xs tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-3">
                {book.episode.brand.name}
              </div>
              <h2 className="text-3xl mb-3 group-hover:opacity-70 transition-opacity" style={{ fontFamily: "'EB Garamond', serif" }}>
                {book.title}
              </h2>
              {book.author && (
                <div className="text-gray-600 dark:text-gray-400 mb-3">
                  by {book.author}
                </div>
              )}
            </div>
          </div>
          {book.description && (
            <p className="text-gray-700 dark:text-gray-300 mb-3">
              {book.description}
            </p>
          )}
          <div className="text-sm text-gray-600 dark:text-gray-400">
            {book.episode.brand.station.name}
            {book.episode.aired_at && (
              <> · {formatDateLong(book.episode.aired_at)}</>
            )}
          </div>
        </article>
      </a>
    )
  }

  return (
    <a
      href={`/${book.episode.brand.slug}/${book.slug}`}
      className="group block border-b border-gray-200 dark:border-gray-800 py-6 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors -mx-4 px-4"
    >
      <article className="flex gap-4">
        {book.cover_image && (
          <div className="flex-shrink-0 w-16">
            <ImageWithFallback
              src={book.cover_image}
              alt={`Cover of ${book.title}`}
              className="w-full h-auto shadow"
            />
          </div>
        )}
        <div className="flex-1">
          <div className="text-xs tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-2">
            {book.episode.brand.name}
          </div>
          <h3 className="mb-1 group-hover:opacity-70 transition-opacity" style={{ fontFamily: "'EB Garamond', serif" }}>
            {book.title}
          </h3>
          {book.author && (
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              by {book.author}
            </div>
          )}
          <div className="text-sm text-gray-500 dark:text-gray-500">
            {book.episode.brand.station.name}
            {book.episode.title && (
              <> · {truncateAtWord(book.episode.title, 50)}</>
            )}
            {book.episode.aired_at && (
              <> · {formatDateShort(book.episode.aired_at)}</>
            )}
          </div>
        </div>
      </article>
    </a>
  )
}

