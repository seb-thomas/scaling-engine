import { Link, useLocation } from 'react-router-dom'
import { Menu } from 'lucide-react'
import { Button } from './ui/button'

export function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100">
      <header className="border-b border-gray-200 dark:border-gray-800">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" className="md:hidden">
                <Menu className="w-5 h-5" />
              </Button>
            </div>
            
            <Link to="/" className="absolute left-1/2 -translate-x-1/2">
              <div className="flex items-center gap-2">
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 32 32"
                  fill="none"
                  className="text-gray-900 dark:text-gray-100"
                >
                  <path
                    d="M2 10 Q 4 8, 6 10 T 10 10 T 14 10 T 18 10 T 22 10 T 26 10 T 30 10"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    fill="none"
                  />
                  <path
                    d="M2 16 Q 4 14, 6 16 T 10 16 T 14 16 T 18 16 T 22 16 T 26 16 T 30 16"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    fill="none"
                  />
                  <path
                    d="M2 22 Q 4 20, 6 22 T 10 22 T 14 22 T 18 22 T 22 22 T 26 22 T 30 22"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    fill="none"
                  />
                </svg>
                <span
                  className="text-2xl italic"
                  style={{ fontFamily: "'EB Garamond', serif", letterSpacing: '-0.02em' }}
                >
                  Radio Reads
                </span>
              </div>
            </Link>
          </div>

          <nav className="hidden md:flex items-center gap-6 py-4 border-t border-gray-200 dark:border-gray-800">
            <Link
              to="/"
              className={`hover:opacity-70 transition-opacity ${location.pathname === '/' ? 'opacity-100' : 'opacity-70'}`}
            >
              Latest Books
            </Link>
            <Link
              to="/books"
              className={`hover:opacity-70 transition-opacity ${location.pathname === '/books' ? 'opacity-100' : 'opacity-70'}`}
            >
              All Books
            </Link>
            <Link
              to="/shows"
              className={`hover:opacity-70 transition-opacity ${location.pathname === '/shows' ? 'opacity-100' : 'opacity-70'}`}
            >
              All Shows
            </Link>
          </nav>
        </div>
      </header>

      <main className="pb-16">{children}</main>

      <footer className="border-t border-gray-200 dark:border-gray-800 mt-24">
        <div className="container mx-auto px-4 py-12 text-center text-gray-600 dark:text-gray-400">
          <p>Radio Reads &copy; {new Date().getFullYear()}</p>
        </div>
      </footer>
    </div>
  )
}

