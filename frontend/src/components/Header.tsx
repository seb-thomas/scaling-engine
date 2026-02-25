import { useState } from 'react'
import { Menu, X } from 'lucide-react'
import { Button } from './ui/button'

interface HeaderProps {
  pathname: string
}

function NavLink({ href, active, children }: { href: string; active: boolean; children: React.ReactNode }) {
  return (
    <a
      href={href}
      className={`pb-1 transition-colors ${
        active
          ? 'text-gray-900 dark:text-gray-100'
          : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
      }`}
    >
      {children}
    </a>
  )
}

export function Header({ pathname }: HeaderProps) {
  const [mobileOpen, setMobileOpen] = useState(false)

  const links = [
    { href: '/', label: 'Latest', active: pathname === '/' },
    { href: '/books', label: 'All Books', active: pathname === '/books' },
    { href: '/shows', label: 'Shows', active: pathname === '/shows' || pathname.startsWith('/show/') },
    { href: '/topics', label: 'Topics', active: pathname === '/topics' || pathname.startsWith('/topic/') },
  ]

  return (
    <header>
      <div className="container border-b md:border-b-0 border-gray-200 dark:border-gray-800">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileOpen(!mobileOpen)}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
          </div>

          <a href="/" className="absolute left-1/2 -translate-x-1/2">
            <div className="flex items-center gap-2">
              <svg
                width="32"
                height="32"
                viewBox="0 0 32 32"
                fill="none"
                className="relative top-px text-gray-900 dark:text-gray-100"
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
              <span className="font-serif text-[1.8rem] italic tracking-tight">
                Radio Reads
              </span>
            </div>
          </a>
        </div>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6 py-4 border-t border-b border-gray-200 dark:border-gray-800">
          {links.map((link) => (
            <NavLink key={link.href} href={link.href} active={link.active}>
              {link.label}
            </NavLink>
          ))}
        </nav>

        {/* Mobile nav */}
        {mobileOpen && (
          <nav className="md:hidden flex flex-col gap-4 py-4 border-t border-gray-200 dark:border-gray-800">
            {links.map((link) => (
              <NavLink key={link.href} href={link.href} active={link.active}>
                {link.label}
              </NavLink>
            ))}
          </nav>
        )}
      </div>
    </header>
  )
}
