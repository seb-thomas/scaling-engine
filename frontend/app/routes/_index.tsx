import { Link, useLoaderData } from 'react-router-dom'
import { BookCard } from '../../src/components/BookCard'
import { ShowCard } from '../../src/components/ShowCard'
import { fetchBooks, fetchShows } from '../../src/api/client'
import type { Book, Show } from '../../src/types'

export async function loader() {
  const [books, showsData] = await Promise.all([
    fetchBooks(1, 8),
    fetchShows().catch(() => [])
  ])

  const shows = Array.isArray(showsData) 
    ? showsData 
    : showsData.results || []

  return {
    books,
    shows
  }
}

type LoaderData = Awaited<ReturnType<typeof loader>>

export default function HomePage() {
  const data = useLoaderData() as LoaderData
  const { books, shows } = data

  const latestBooks = books.results.slice(0, 8)

  return (
    <div className="container mx-auto px-4 py-12">
      <section className="mb-16">
        <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
          <h1 className="text-sm tracking-wider uppercase mb-4">Latest Books</h1>
        </div>

        <div className="max-w-4xl">
          {latestBooks.map((book: Book, index: number) => (
            <BookCard
              key={book.id}
              book={book}
              featured={index === 0 && !!book.description}
            />
          ))}
          
          <div className="mt-8 text-left">
            <Link 
              to="/books" 
              className="text-sm hover:opacity-70 transition-opacity"
            >
              All books →
            </Link>
          </div>
        </div>
      </section>

      {shows.length > 0 && (
        <section>
          <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
            <h2 className="text-sm tracking-wider uppercase mb-4">Top Shows</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {shows.slice(0, 6).map((show: Show) => (
              <ShowCard key={show.id} show={show} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

