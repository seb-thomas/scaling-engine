import { useState, useEffect } from 'react'
import { BookCard } from '@/components/BookCard'
import { ShowCard } from '@/components/ShowCard'
import { Pagination } from '@/components/Pagination'
import { fetchBooks, fetchShows } from '@/api/client'
import type { Book, Show, PaginatedResponse } from '@/types'

export function HomePage() {
  const [currentPage, setCurrentPage] = useState(1)
  const [books, setBooks] = useState<PaginatedResponse<Book> | null>(null)
  const [shows, setShows] = useState<Show[]>([])
  const booksPerPage = 10

  useEffect(() => {
    fetchBooks(currentPage, booksPerPage).then(setBooks).catch(console.error)
    fetchShows().then(data => {
      console.log('Shows data:', data)
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
  }, [currentPage])

  if (!books) {
    return <div className="container mx-auto px-4 py-12">Loading...</div>
  }

  const totalPages = Math.ceil(books.count / booksPerPage)
  const currentBooks = books.results

  return (
    <div className="container mx-auto px-4 py-12">
      <section className="mb-16">
        <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
          <h1 className="text-sm tracking-wider uppercase mb-4">Latest Books</h1>
        </div>

        <div className="max-w-4xl">
          {currentBooks.map((book, index) => (
            <BookCard
              key={book.id}
              book={book}
              featured={currentPage === 1 && index === 0 && !!book.description}
            />
          ))}
        </div>

        {totalPages > 1 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        )}
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

