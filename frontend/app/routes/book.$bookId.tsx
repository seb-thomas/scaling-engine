import { useLoaderData, Link, type LoaderFunctionArgs } from 'react-router-dom'
import { ArrowLeft, ExternalLink } from 'lucide-react'
import { ImageWithFallback } from '../../src/components/ImageWithFallback'
import { Breadcrumbs } from '../../src/components/Breadcrumbs'
import { Button } from '../../src/components/ui/button'
import { AffiliateDisclosure } from '../../src/components/AffiliateDisclosure'
import { fetchBook } from '../../src/api/client'

export async function loader({ params }: LoaderFunctionArgs) {
  const { bookId } = params
  if (!bookId) {
    throw new Response('Book not found', { status: 404 })
  }

  const book = await fetchBook(Number(bookId))
  if (!book) {
    throw new Response('Book not found', { status: 404 })
  }

  return { book }
}

type LoaderData = Awaited<ReturnType<typeof loader>>

export default function BookDetailPage() {
  const data = useLoaderData() as LoaderData
  const { book } = data

  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    { label: book.episode.brand.station.name, href: `/station/${book.episode.brand.station.station_id}` },
    { label: book.episode.brand.name, href: `/show/${book.episode.brand.id}` },
    { label: book.title }
  ]

  return (
    <div className="container mx-auto px-4 py-12">
      <Breadcrumbs items={breadcrumbItems} />

      <div className="max-w-3xl">
        <Link
          to={`/show/${book.episode.brand.id}`}
          className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to all books
        </Link>

        <article>
          <div className="flex gap-8 mb-8">
            {book.cover_image && (
              <div className="flex-shrink-0 w-48">
                <ImageWithFallback
                  src={book.cover_image}
                  alt={`Cover of ${book.title}`}
                  className="w-full h-auto shadow-xl"
                />
              </div>
            )}
            <div className="flex-1">
              <div className="text-xs tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-4">
                {book.episode.brand.name}
              </div>

              <h1 className="text-5xl mb-6" style={{ fontFamily: "'EB Garamond', serif" }}>
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
            <div className="mb-2">
              <Link
                to={`/show/${book.episode.brand.id}`}
                className="hover:opacity-70 transition-opacity"
              >
                {book.episode.brand.name}, {book.episode.brand.station.name}
              </Link>
            </div>
          </div>

          <div className="mb-8">
            <h2 className="text-sm tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-3">
              Episode
            </h2>
            <p className="italic mb-2">{book.episode.title}</p>
            {book.episode.aired_at && (
              <div className="text-sm text-gray-500 dark:text-gray-500 mb-3">
                {new Date(book.episode.aired_at).toLocaleDateString('en-US', {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric'
                })}
              </div>
            )}
            {book.episode.url && (
              <a
                href={book.episode.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors underline"
              >
                Listen to episode
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
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

