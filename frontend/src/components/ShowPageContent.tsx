import { useState, useEffect } from 'react'
import { Breadcrumbs } from './Breadcrumbs'
import { BookCard } from './BookCard'
import { Pagination } from './Pagination'
import type { Book, Show } from '../types'

interface ShowPageContentProps {
  initialShow: Show
  initialBooks: { results: Book[]; count: number }
  initialPage?: number
}

export function ShowPageContent({ 
  initialShow, 
  initialBooks, 
  initialPage = 1 
}: ShowPageContentProps) {
  const [books, setBooks] = useState(initialBooks)
  const [currentPage, setCurrentPage] = useState(initialPage)
  const [isLoading, setIsLoading] = useState(false)
  const booksPerPage = 10

  // Fetch books when page changes
  useEffect(() => {
    const fetchBooks = async () => {
      setIsLoading(true)
      try {
        const response = await fetch(`/api/books/?brand_slug=${initialShow.slug}&page=${currentPage}&page_size=${booksPerPage}`)
        if (!response.ok) throw new Error('Failed to fetch show books')
        const data = await response.json()
        const booksData = data.results
          ? data
          : { count: data.length, results: data, next: null, previous: null }
        setBooks(booksData)

        // Update URL without page reload
        const newUrl = `/show/${initialShow.slug}?page=${currentPage}`
        window.history.replaceState({}, '', newUrl)
      } catch (error) {
        console.error('Error fetching books:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchBooks()
  }, [currentPage, initialShow.slug])

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    { label: initialShow.station.name, href: `/station/${initialShow.station.station_id}` },
    { label: initialShow.name }
  ]

  const totalPages = Math.ceil(books.count / booksPerPage)

  return (
    <div className="container py-12">
      <Breadcrumbs items={breadcrumbItems} />

      <div className="mb-12">
        <div className="text-xs tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-3">
          {initialShow.station.name}
        </div>
        <h1 className="font-serif text-3xl font-medium mb-4">
          {initialShow.name}
        </h1>
        {initialShow.description && (
          <p className="text-gray-700 dark:text-gray-400 mb-2">
            {initialShow.description}
          </p>
        )}
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {initialShow.book_count.toLocaleString()} book{initialShow.book_count !== 1 ? 's' : ''} discovered
        </p>
      </div>

      <div>
        <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
          <h2 className="text-sm tracking-wider uppercase mb-4">Books</h2>
        </div>

        <div className="max-w-4xl">
          {isLoading ? (
            <p className="text-center py-12 text-gray-600 dark:text-gray-400">Loading...</p>
          ) : (
            <>
              {books.results.map((book: Book) => (
                <BookCard key={book.id} book={book} />
              ))}

              {totalPages > 1 && (
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

