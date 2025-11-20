import { useState, useEffect } from 'react'
import { Search } from 'lucide-react'
import { BookCard } from '@/components/BookCard'
import { Pagination } from '@/components/Pagination'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { fetchBooks } from '@/api/client'
import type { Book, PaginatedResponse } from '@/types'

export function AllBooksPage() {
  const [currentPage, setCurrentPage] = useState(1)
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [books, setBooks] = useState<PaginatedResponse<Book> | null>(null)
  const booksPerPage = 10

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
      setCurrentPage(1) // Reset to first page on search
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Fetch books with search
  useEffect(() => {
    fetchBooks(
      currentPage,
      booksPerPage,
      debouncedSearch || undefined
    ).then(setBooks).catch(console.error)
  }, [currentPage, debouncedSearch])

  if (!books) {
    return <div className="container mx-auto px-4 py-12">Loading...</div>
  }

  const totalPages = Math.ceil(books.count / booksPerPage)
  const currentBooks = books.results

  return (
    <div className="container mx-auto px-4 py-12">
      <Breadcrumbs items={[{ label: 'All Books' }]} />

      <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
        <h1 className="text-sm tracking-wider uppercase mb-4">
          All Books
        </h1>
      </div>

      {/* Search Box */}
      <div className="max-w-4xl mb-12">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 size-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search books by title, author, or description..."
            className="w-full pl-12 pr-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 focus:outline-none focus:border-gray-400 dark:focus:border-gray-600 transition-colors"
          />
        </div>
        {searchQuery && (
          <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            Found {books.count} book
            {books.count !== 1 ? 's' : ''} matching "
            {searchQuery}"
          </p>
        )}
      </div>

      {/* Books List */}
      <div className="max-w-4xl">
        {currentBooks.length > 0 ? (
          <>
            {currentBooks.map((book) => (
              <BookCard
                key={book.id}
                book={book}
                featured={false}
              />
            ))}

            {totalPages > 1 && (
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={setCurrentPage}
              />
            )}
          </>
        ) : (
          <p className="text-center py-12 text-gray-600 dark:text-gray-400">
            No books found matching your search.
          </p>
        )}
      </div>
    </div>
  )
}

