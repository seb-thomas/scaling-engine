import { useState, useEffect, useRef } from 'react'
import { Breadcrumbs } from './Breadcrumbs'
import { BookCard } from './BookCard'
import { Pagination } from './Pagination'
import type { Book, Topic } from '../types'

interface TopicPageContentProps {
  initialTopic: Topic
  initialBooks: { results: Book[]; count: number }
  initialPage?: number
}

export function TopicPageContent({
  initialTopic,
  initialBooks,
  initialPage = 1,
}: TopicPageContentProps) {
  const [books, setBooks] = useState(initialBooks)
  const [currentPage, setCurrentPage] = useState(initialPage)
  const [isLoading, setIsLoading] = useState(false)
  const isInitialMount = useRef(true)
  const booksPerPage = 10

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false
      return
    }

    const fetchBooks = async () => {
      setIsLoading(true)
      try {
        const response = await fetch(
          `/api/books/?topic=${initialTopic.slug}&page=${currentPage}&page_size=${booksPerPage}`
        )
        if (!response.ok) throw new Error('Failed to fetch topic books')
        const data = await response.json()
        const booksData = data.results
          ? data
          : { count: data.length, results: data, next: null, previous: null }
        setBooks(booksData)

        const newUrl = `/topic/${initialTopic.slug}?page=${currentPage}`
        window.history.replaceState({}, '', newUrl)
      } catch (error) {
        console.error('Error fetching books:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchBooks()
  }, [currentPage, initialTopic.slug])

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const totalPages = Math.ceil(books.count / booksPerPage)

  return (
    <div className="container py-12">
      <Breadcrumbs
        items={[
          { label: 'Home', href: '/' },
          { label: 'Topics', href: '/topics' },
          { label: initialTopic.name },
        ]}
      />

      <div className="mb-12">
        <h1 className="font-serif text-2xl font-medium mb-2">
          {initialTopic.name}
        </h1>
        {initialTopic.description && (
          <p className="text-gray-600 dark:text-gray-400 mb-2">
            {initialTopic.description}
          </p>
        )}
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {initialTopic.book_count.toLocaleString()} book
          {initialTopic.book_count !== 1 ? 's' : ''} discovered
        </p>
      </div>

      <div>
        <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
          <h2 className="text-sm tracking-wider uppercase mb-4">Books</h2>
        </div>

        <div className="max-w-4xl">
          {isLoading ? (
            <p className="text-center py-12 text-gray-600 dark:text-gray-400">
              Loading...
            </p>
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
