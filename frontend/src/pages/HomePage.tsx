import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { BookCard } from '@/components/BookCard'
import { ShowCard } from '@/components/ShowCard'
import { fetchBooks, fetchShows } from '@/api/client'
import type { Book, Show, PaginatedResponse } from '@/types'

export function HomePage() {
  const [books, setBooks] = useState<PaginatedResponse<Book> | null>(null)
  const [shows, setShows] = useState<Show[]>([])

  // Fetch shows
  useEffect(() => {
    fetchShows().then(data => {
      if (Array.isArray(data)) {
        setShows(data)
      } else if (data.results) {
        setShows(data.results)
      } else {
        setShows([])
      }
    }).catch(err => {
      console.error('Error fetching shows:', err)
      setShows([])
    })
  }, [])

  // Fetch latest 8 books
  useEffect(() => {
    fetchBooks(1, 8).then(setBooks).catch(console.error)
  }, [])

  if (!books) {
    return <div className="container mx-auto px-4 py-12">Loading...</div>
  }

  const latestBooks = books.results.slice(0, 8)

  return (
    <div className="container mx-auto px-4 py-12">
      <section className="mb-16">
        <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
          <h1 className="text-sm tracking-wider uppercase mb-4">Latest Books</h1>
        </div>

        <div className="max-w-4xl">
          {latestBooks.map((book, index) => (
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
            {shows.slice(0, 6).map(show => (
              <ShowCard key={show.id} show={show} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

