import { useState, useEffect, useMemo } from 'react'
import { Search, X } from 'lucide-react'
import { BookCard } from '@/components/BookCard'
import { ShowCard } from '@/components/ShowCard'
import { Pagination } from '@/components/Pagination'
import { fetchBooks, fetchShows, fetchStations } from '@/api/client'
import type { Book, Show, Station, PaginatedResponse } from '@/types'

export function HomePage() {
  const [currentPage, setCurrentPage] = useState(1)
  const [books, setBooks] = useState<PaginatedResponse<Book> | null>(null)
  const [shows, setShows] = useState<Show[]>([])
  const [stations, setStations] = useState<Station[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedStation, setSelectedStation] = useState<string>('')
  const [selectedShow, setSelectedShow] = useState<number | null>(null)
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const booksPerPage = 10

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
      setCurrentPage(1) // Reset to first page on search
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Fetch stations and shows
  useEffect(() => {
    fetchStations().then(data => {
      if (Array.isArray(data)) {
        setStations(data)
      } else if (data.results) {
        setStations(data.results)
      }
    }).catch(console.error)

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

  // Filter shows by selected station
  const filteredShows = useMemo(() => {
    if (!selectedStation) return shows
    return shows.filter(show => show.station?.station_id === selectedStation)
  }, [shows, selectedStation])

  // Fetch books with search and filters
  useEffect(() => {
    fetchBooks(
      currentPage,
      booksPerPage,
      debouncedSearch || undefined,
      selectedStation || undefined,
      selectedShow || undefined
    ).then(setBooks).catch(console.error)
  }, [currentPage, debouncedSearch, selectedStation, selectedShow])

  const handleClearFilters = () => {
    setSearchQuery('')
    setSelectedStation('')
    setSelectedShow(null)
    setCurrentPage(1)
  }

  const hasActiveFilters = searchQuery || selectedStation || selectedShow

  if (!books) {
    return <div className="container mx-auto px-4 py-12">Loading...</div>
  }

  const totalPages = Math.ceil(books.count / booksPerPage)
  const currentBooks = books.results

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

        {/* Search and Filters */}
        <div className="mb-8 space-y-4">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search books by title, author, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          <div className="flex flex-wrap gap-4 items-center">
            <select
              value={selectedStation}
              onChange={(e) => {
                setSelectedStation(e.target.value)
                setSelectedShow(null) // Reset show when station changes
                setCurrentPage(1)
              }}
              className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-orange-500"
            >
              <option value="">All Stations</option>
              {stations.map(station => (
                <option key={station.id} value={station.station_id}>
                  {station.name}
                </option>
              ))}
            </select>

            {selectedStation && (
              <select
                value={selectedShow || ''}
                onChange={(e) => {
                  setSelectedShow(e.target.value ? Number(e.target.value) : null)
                  setCurrentPage(1)
                }}
                className="px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-md bg-white dark:bg-gray-900 focus:outline-none focus:ring-2 focus:ring-orange-500"
              >
                <option value="">All Shows</option>
                {filteredShows.map(show => (
                  <option key={show.id} value={show.id}>
                    {show.name}
                  </option>
                ))}
              </select>
            )}

            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
              >
                Clear filters
              </button>
            )}
          </div>
        </div>

        {currentBooks.length === 0 ? (
          <div className="text-center py-12 text-gray-600 dark:text-gray-400">
            <p>No books found matching your search criteria.</p>
          </div>
        ) : (
          <>
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
          </>
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

