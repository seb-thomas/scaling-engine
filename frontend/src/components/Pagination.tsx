import { ChevronLeft, ChevronRight } from 'lucide-react'

type PaginationProps = {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1)
  
  // Show max 7 page numbers
  let visiblePages: (number | -1)[] = pages
  if (totalPages > 7) {
    if (currentPage <= 4) {
      visiblePages = [...pages.slice(0, 5), -1, totalPages]
    } else if (currentPage >= totalPages - 3) {
      visiblePages = [1, -1, ...pages.slice(totalPages - 5)]
    } else {
      visiblePages = [1, -1, currentPage - 1, currentPage, currentPage + 1, -1, totalPages]
    }
  }

  return (
    <div className="flex items-center justify-center gap-1 mt-12">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 hover:opacity-70 disabled:opacity-30 cursor-default transition-opacity"
        aria-label="Previous page"
      >
        <ChevronLeft className="size-4" />
      </button>

      <div className="flex items-center gap-1 mx-2">
        {visiblePages.map((page, index) => (
          page === -1 ? (
            <span key={`ellipsis-${index}`} className="px-3 py-2 text-gray-400">···</span>
          ) : (
            <button
              key={page}
              onClick={() => onPageChange(page)}
              className="min-w-10 px-3 py-2 transition-all relative"
            >
              <span className="relative z-10">{page}</span>
              {currentPage === page && (
                <span 
                  className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-1"
                  style={{
                    backgroundImage: `url("data:image/svg+xml,%3Csvg width='32' height='4' viewBox='0 0 32 4' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M2 2 Q 4 0, 6 2 T 10 2 T 14 2 T 18 2 T 22 2 T 26 2 T 30 2' stroke='%23C85A3A' stroke-width='1.5' fill='none'/%3E%3C/svg%3E")`,
                    backgroundSize: '100% 100%',
                    backgroundRepeat: 'no-repeat'
                  }}
                />
              )}
            </button>
          )
        ))}
      </div>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 hover:opacity-70 disabled:opacity-30 cursor-default transition-opacity"
        aria-label="Next page"
      >
        <ChevronRight className="size-4" />
      </button>
    </div>
  )
}

