import { Breadcrumbs } from './Breadcrumbs'
import { ShowCard } from './ShowCard'
import type { Show, Station } from '../types'

interface StationPageContentProps {
  station: Station
  shows: Show[]
}

export function StationPageContent({ station, shows }: StationPageContentProps) {
  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    { label: station.name }
  ]

  return (
    <div className="container py-12">
      <Breadcrumbs items={breadcrumbItems} />

      <div className="mb-12">
        <h1 className="font-serif text-4xl mb-4">
          {station.name}
        </h1>
        {station.description && (
          <p className="text-gray-700 dark:text-gray-400 mb-4 max-w-2xl">
            {station.description}
          </p>
        )}
        <div className="flex items-center gap-4">
          {station.station_id === 'npr' ? (
            <a
              href="https://www.npr.org/support"
              target="_blank"
              rel="noopener"
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-orange-700 dark:hover:text-orange-400 transition-colors"
            >
              Support NPR &rarr;
            </a>
          ) : station.url && (
            <a
              href={station.url}
              target="_blank"
              rel="noopener"
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-orange-700 dark:hover:text-orange-400 transition-colors"
            >
              Visit {station.name} &rarr;
            </a>
          )}
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          {shows.length} show{shows.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div>
        <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
          <h2 className="text-sm tracking-wider uppercase mb-4">Shows</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {shows.map((show: Show) => (
            <ShowCard key={show.id} show={show} />
          ))}
        </div>
      </div>
    </div>
  )
}
