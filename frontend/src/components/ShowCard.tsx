import { Link } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import type { Show } from '@/types'

type ShowCardProps = {
  show: Show
}

function getShowColor(brandColor: string | undefined, stationId: string): { light: string; dark: string } {
  if (brandColor) {
    // Use the persisted brand color for light mode
    // For dark mode, use a slightly lighter version (add ~20% brightness)
    // Simple approach: if it's a hex color, we'll use it as-is for both
    // In practice, you might want to adjust the dark color, but for now use the same
    return { light: brandColor, dark: brandColor }
  }
  // Fallback to default colors based on station
  return stationId === 'bbc' 
    ? { light: '#8b4513', dark: '#a0522d' }
    : { light: '#1e3a5f', dark: '#2d5986' }
}

export function ShowCard({ show }: ShowCardProps) {
  const colors = getShowColor(show.brand_color, show.station.station_id)

  const wavePattern = (color: string) => 
    `data:image/svg+xml,%3Csvg width='32' height='24' viewBox='0 0 32 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M2 6 Q 4 4, 6 6 T 10 6 T 14 6 T 18 6 T 22 6 T 26 6 T 30 6' stroke='${encodeURIComponent(color)}' stroke-width='1.5' fill='none'/%3E%3Cpath d='M2 12 Q 4 10, 6 12 T 10 12 T 14 12 T 18 12 T 22 12 T 26 12 T 30 12' stroke='${encodeURIComponent(color)}' stroke-width='1.5' fill='none'/%3E%3Cpath d='M2 18 Q 4 16, 6 18 T 10 18 T 14 18 T 18 18 T 22 18 T 26 18 T 30 18' stroke='${encodeURIComponent(color)}' stroke-width='1.5' fill='none'/%3E%3C/svg%3E`

  return (
    <article className="group block">
      <Link to={`/show/${show.id}`} className="block">
        {/* Wave pattern masthead */}
        <div className="mb-4 overflow-hidden h-6">
          <div
            className="h-6 dark:hidden"
            style={{
              backgroundImage: `url("${wavePattern(colors.light)}")`,
              backgroundRepeat: 'repeat',
              backgroundSize: '32px 24px'
            }}
          />
          <div
            className="h-6 hidden dark:block"
            style={{
              backgroundImage: `url("${wavePattern(colors.dark)}")`,
              backgroundRepeat: 'repeat',
              backgroundSize: '32px 24px'
            }}
          />
        </div>

        {/* Content */}
        <div>
          <div className="text-xs tracking-wider uppercase text-gray-600 dark:text-gray-400 mb-2 group-hover:text-orange-700 dark:group-hover:text-orange-400 transition-colors">
            {show.station.name}
          </div>
          <h3 className="text-xl mb-2 group-hover:text-orange-900 dark:group-hover:text-orange-100 transition-colors leading-tight" style={{ fontFamily: "'EB Garamond', serif" }}>
            {show.name}
          </h3>
          {show.description && (
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-3 line-clamp-2">
              {show.description}
            </p>
          )}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600 dark:text-gray-400 group-hover:text-orange-800 dark:group-hover:text-orange-300 transition-colors">
              {show.book_count.toLocaleString()} books
            </div>
            <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-orange-700 dark:group-hover:text-orange-400 transition-colors group-hover:translate-x-1 transition-transform" />
          </div>
        </div>
      </Link>
    </article>
  )
}

