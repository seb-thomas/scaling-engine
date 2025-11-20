import { useState, useEffect } from "react";
import {
  useLoaderData,
  useSearchParams,
  useNavigate,
  type LoaderFunctionArgs,
} from "react-router-dom";
import { Search } from "lucide-react";
import { BookCard } from "../../src/components/BookCard";
import { Pagination } from "../../src/components/Pagination";
import { Breadcrumbs } from "../../src/components/Breadcrumbs";
import { fetchBooks } from "../../src/api/client";
import type { Book } from "../../src/types";

export async function loader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const page = parseInt(url.searchParams.get("page") || "1", 10);
  const search = url.searchParams.get("search") || undefined;
  const booksPerPage = 10;

  const books = await fetchBooks(page, booksPerPage, search);
  return { books, search: search || "" };
}

type LoaderData = Awaited<ReturnType<typeof loader>>;

export default function AllBooksPage() {
  const data = useLoaderData() as LoaderData;
  const { books, search: initialSearch } = data;
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState(initialSearch);
  const [, setDebouncedSearch] = useState(initialSearch);
  const booksPerPage = 10;

  const currentPage = parseInt(searchParams.get("page") || "1", 10);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      // Update URL when search changes
      const newParams = new URLSearchParams(searchParams);
      if (searchQuery) {
        newParams.set("search", searchQuery);
        newParams.set("page", "1"); // Reset to first page on search
      } else {
        newParams.delete("search");
        newParams.set("page", "1");
      }
      navigate(`/books?${newParams.toString()}`, { replace: true });
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, searchParams, navigate]);

  const handlePageChange = (page: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set("page", page.toString());
    navigate(`/books?${newParams.toString()}`);
  };

  const totalPages = Math.ceil(books.count / booksPerPage);
  const currentBooks = books.results;

  return (
    <div className="container mx-auto px-4 py-12">
      <Breadcrumbs items={[{ label: "All Books" }]} />

      <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
        <h1 className="text-sm tracking-wider uppercase mb-4">All Books</h1>
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
            {books.count !== 1 ? "s" : ""} matching "{searchQuery}"
          </p>
        )}
      </div>

      {/* Books List */}
      <div className="max-w-4xl">
        {currentBooks.length > 0 ? (
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
