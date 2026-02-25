import { useState, useEffect, useRef } from "react";
import { Search } from "lucide-react";
import { BookCard } from "./BookCard";
import { Pagination } from "./Pagination";
import { Breadcrumbs } from "./Breadcrumbs";
import type { Book } from "../types";

interface BooksPageContentProps {
  initialBooks: { results: Book[]; count: number };
  initialSearch?: string;
  initialPage?: number;
}

export function BooksPageContent({
  initialBooks,
  initialSearch = "",
  initialPage = 1,
}: BooksPageContentProps) {
  const [searchQuery, setSearchQuery] = useState(initialSearch);
  const [debouncedSearch, setDebouncedSearch] = useState(initialSearch);
  const [books, setBooks] = useState(initialBooks);
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [isLoading, setIsLoading] = useState(false);
  const booksPerPage = 10;
  
  // Track if this is the initial mount to avoid refetching SSR data
  const isInitialMount = useRef(true);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      // Only reset page if search actually changed (not on initial mount)
      if (searchQuery !== initialSearch || !isInitialMount.current) {
        setCurrentPage(1);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, initialSearch]);

  // Fetch books when search or page changes
  useEffect(() => {
    // Skip fetch on initial mount - we already have SSR data
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    const fetchBooks = async () => {
      setIsLoading(true);
      try {
        const params = new URLSearchParams({
          page: currentPage.toString(),
          page_size: booksPerPage.toString(),
        });
        
        if (debouncedSearch) {
          params.append("search", debouncedSearch);
        }
        const response = await fetch(`/api/books/?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to fetch books');
        const data = await response.json();
        const booksData = data.results
          ? data
          : { count: data.length, results: data, next: null, previous: null };
        setBooks(booksData);

        // Update URL without page reload
        const newUrl = `/books?${params.toString()}`;
        window.history.replaceState({}, '', newUrl);
      } catch (error) {
        console.error('Error fetching books:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchBooks();
  }, [debouncedSearch, currentPage]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const totalPages = Math.ceil(books.count / booksPerPage);
  const currentBooks = books.results;

  return (
    <div className="container py-12">
      <Breadcrumbs items={[{ label: "All Books" }]} />

      <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
        <h1 className="text-sm tracking-wider uppercase mb-4">All Books</h1>
      </div>

      {/* Search */}
      <div className="max-w-4xl mb-12">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 size-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title, author, or topic..."
            className="w-full pl-12 pr-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 focus:outline-none focus:border-gray-400 dark:focus:border-gray-600 transition-colors"
          />
        </div>
        {searchQuery && (
          <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
            Found {books.count} book
            {books.count !== 1 ? "s" : ""}
            {" "}matching &ldquo;{searchQuery}&rdquo;
          </p>
        )}
      </div>

      {/* Books List */}
      <div className="max-w-4xl">
        {isLoading ? (
          <p className="text-center py-12 text-gray-600 dark:text-gray-400">Loading...</p>
        ) : currentBooks.length > 0 ? (
          <>
            {currentBooks.map((book: Book) => (
              <BookCard key={book.id} book={book} featured={false} />
            ))}

            {totalPages > 1 && (
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={handlePageChange}
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
  );
}

