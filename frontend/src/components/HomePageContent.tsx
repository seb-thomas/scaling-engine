import { BookCard } from './BookCard'
import { ShowCard } from './ShowCard'
import type { Book, Show } from '../types'

interface HomePageContentProps {
  books: { results: Book[]; count: number }
  shows: Show[]
}

export function HomePageContent({ books, shows }: HomePageContentProps) {
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
            <a 
              href="/books" 
              className="text-sm hover:opacity-70 transition-opacity"
            >
              All books →
            </a>
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

