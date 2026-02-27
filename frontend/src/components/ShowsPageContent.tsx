import { Breadcrumbs } from './Breadcrumbs'
import { ShowCard } from './ShowCard'
import type { Show, Station } from '../types'

interface ShowsPageContentProps {
  shows: Show[]
  stations: Station[]
}

export function ShowsPageContent({ shows, stations }: ShowsPageContentProps) {
  // Group shows by station
  const showsByStation = stations.map((station: Station) => ({
    station,
    shows: shows.filter((show: Show) => show.station?.station_id === station.station_id)
  })).filter((group: { station: Station; shows: Show[] }) => group.shows.length > 0)

  return (
    <div className="container py-12">
      <Breadcrumbs
        items={[
          { label: 'Home', href: '/' },
          { label: 'Shows' }
        ]}
      />

      <div className="mb-12">
        <h1 className="text-2xl font-medium mb-4">Shows</h1>
        <p className="text-gray-700 dark:text-gray-400">
          Explore all radio shows from {stations.map((s: Station) => s.name).join(' and ')}
        </p>
      </div>

      {showsByStation.map(({ station, shows: stationShows }: { station: Station; shows: Show[] }, index: number) => (
        <section key={station.id} className={index < showsByStation.length - 1 ? 'mb-16' : ''}>
          <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
            <a
              href={`/station/${station.station_id}`}
              className="hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <h2 className="text-sm tracking-wider uppercase mb-4">{station.name}</h2>
            </a>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {stationShows.map((show: Show) => (
              <ShowCard key={show.id} show={show} />
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}

