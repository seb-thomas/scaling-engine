import { useLoaderData, useSearchParams, useNavigate, type LoaderFunctionArgs } from 'react-router-dom'
import { Breadcrumbs } from '../../src/components/Breadcrumbs'
import { BookCard } from '../../src/components/BookCard'
import { Pagination } from '../../src/components/Pagination'
import { fetchShow, fetchShowBooks } from '../../src/api/client'
import type { Book } from '../../src/types'

export async function loader({ params, request }: LoaderFunctionArgs) {
  const showId = Number(params.showId)
  if (!showId) {
    throw new Response('Show not found', { status: 404 })
  }

  const url = new URL(request.url)
  const page = parseInt(url.searchParams.get('page') || '1', 10)
  const booksPerPage = 10

  const [show, books] = await Promise.all([
    fetchShow(showId),
    fetchShowBooks(showId, page, booksPerPage)
  ])

  return { show, books }
}

type LoaderData = Awaited<ReturnType<typeof loader>>

export default function ShowPage() {
  const data = useLoaderData() as LoaderData
  const { show, books } = data
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const booksPerPage = 10

  const currentPage = parseInt(searchParams.get('page') || '1', 10)

  const handlePageChange = (page: number) => {
    const newParams = new URLSearchParams(searchParams)
    newParams.set('page', page.toString())
    navigate(`?${newParams.toString()}`)
  }

  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    { label: show.station.name, href: `/station/${show.station.station_id}` },
    { label: show.name }
  ]

  const totalPages = Math.ceil(books.count / booksPerPage)

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
          {books.results.map((book: Book) => (
            <BookCard key={book.id} book={book} />
          ))}
        </div>

        {totalPages > 1 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />
        )}
      </div>
    </div>
  )
}

