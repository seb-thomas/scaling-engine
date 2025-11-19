import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { BookCard } from '@/components/BookCard'
import { Pagination } from '@/components/Pagination'
import { fetchShow, fetchShowBooks } from '@/api/client'
import type { Show, Book, PaginatedResponse } from '@/types'

export function ShowPage() {
  const { showId } = useParams<{ showId: string }>()
  const [show, setShow] = useState<Show | null>(null)
  const [books, setBooks] = useState<PaginatedResponse<Book> | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const booksPerPage = 10

  useEffect(() => {
    if (!showId) return
    
    fetchShow(Number(showId)).then(setShow).catch(console.error)
  }, [showId])

  useEffect(() => {
    if (!showId) return
    
    fetchShowBooks(Number(showId), currentPage, booksPerPage).then(setBooks).catch(console.error)
  }, [showId, currentPage])

  if (!show) {
    return (
      <div className="container mx-auto px-4 py-12">
        <p>Show not found</p>
      </div>
    )
  }

  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    { label: show.station.name, href: `/station/${show.station.station_id}` },
    { label: show.name }
  ]

  const totalPages = books ? Math.ceil(books.count / booksPerPage) : 0

  return (
    <div className="container mx-auto px-4 py-12">
      <Breadcrumbs items={breadcrumbItems} />

      <div className="mb-12">
        <div className="text-xs tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-3">
          {show.station.name}
        </div>
        <h1 className="text-4xl mb-4" style={{ fontFamily: "'EB Garamond', serif" }}>
          {show.name}
        </h1>
        {show.description && (
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-2">
            {show.description}
          </p>
        )}
        <p className="text-sm text-gray-500 dark:text-gray-500">
          {show.book_count.toLocaleString()} book{show.book_count !== 1 ? 's' : ''} discovered
        </p>
      </div>

      <div>
        <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
          <h2 className="text-sm tracking-wider uppercase mb-4">Books</h2>
        </div>

        <div className="max-w-4xl">
          {books?.results.map(book => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>

        {totalPages > 1 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        )}
      </div>
    </div>
  )
}

