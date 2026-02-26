import { ImageWithFallback } from './ImageWithFallback'
import { formatDateLong, formatDateShort } from '@/lib/utils'
import type { Book } from '@/types'

type BookCardProps = {
  book: Book
  featured?: boolean
}

export function BookCard({ book, featured = false }: BookCardProps) {
  const ep = book.episodes?.[0]
  const brand = ep?.brand

  if (featured) {
    return (
      <a
        href={`/${brand?.slug ?? 'unknown'}/${book.slug}`}
        className="group block"
      >
        <article className="border-b border-gray-200 dark:border-gray-800 pb-8 mb-8">
          <div className="flex gap-6 mb-6">
              <div className="flex-shrink-0 w-32" style={{ containerType: 'inline-size' }}>
                <ImageWithFallback
                  src={book.cover_image}
                  alt={`Cover of ${book.title}`}
                  className="w-full h-auto shadow-lg"
                  title={book.title}
                  author={book.author}
                  brandColor={brand?.brand_color}
                />
              </div>
            <div className="flex-1">
              <h2 className="font-serif text-3xl mb-3 group-hover:opacity-70 transition-opacity">
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
            {brand?.station?.name}
            {ep?.aired_at && (
              <> · {formatDateLong(ep.aired_at)}</>
            )}
          </div>
        </article>
      </a>
    )
  }

  return (
    <a
      href={`/${brand?.slug ?? 'unknown'}/${book.slug}`}
      className="group block border-b border-gray-200 dark:border-gray-800 py-6 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors -mx-4 px-4"
    >
      <article className="flex gap-4">
          <div className="flex-shrink-0 w-16" style={{ containerType: 'inline-size' }}>
            <ImageWithFallback
              src={book.cover_image}
              alt={`Cover of ${book.title}`}
              className="w-full h-auto shadow"
              title={book.title}
              author={book.author}
              brandColor={brand?.brand_color}
            />
          </div>
        <div className="flex-1 flex flex-col">
          <h3 className="font-serif text-lg font-medium mb-1 group-hover:opacity-70 transition-opacity">
            {book.title}
          </h3>
          {book.author && (
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              by {book.author}
            </div>
          )}
          <div className="text-sm text-gray-500 dark:text-gray-400 mt-auto">
            {brand?.station?.name}
            {brand?.name && (
              <> · {brand.name}</>
            )}
            {ep?.aired_at && (
              <> · {formatDateShort(ep.aired_at)}</>
            )}
          </div>
        </div>
      </article>
    </a>
  )
}

