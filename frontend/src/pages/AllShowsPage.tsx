import { Link, useLoaderData } from 'react-router-dom'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { ShowCard } from '@/components/ShowCard'
import { fetchShows, fetchStations } from '@/api/client'
import type { Show, Station } from '@/types'

export async function loader() {
  const [showsData, stationsData] = await Promise.all([
    fetchShows().catch(() => []),
    fetchStations().catch(() => [])
  ])

  const shows = Array.isArray(showsData) 
    ? showsData 
    : showsData.results || []

  const stations = Array.isArray(stationsData)
    ? stationsData
    : stationsData.results || []

  return { shows, stations }
}

export function AllShowsPage() {
  const { shows, stations } = useLoaderData<typeof loader>()

  // Group shows by station
  const showsByStation = stations.map(station => ({
    station,
    shows: shows.filter(show => show.station?.station_id === station.station_id)
  })).filter(group => group.shows.length > 0)

  return (
    <div className="container mx-auto px-4 py-12">
      <Breadcrumbs
        items={[
          { label: 'Home', href: '/' },
          { label: 'All Shows' }
        ]}
      />

      <div className="mb-12">
        <h1 className="text-4xl mb-4">All Shows</h1>
        <p className="text-xl text-gray-600 dark:text-gray-400">
          Explore all radio shows from {stations.map(s => s.name).join(' and ')}
        </p>
      </div>

      {showsByStation.map(({ station, shows: stationShows }, index) => (
        <section key={station.id} className={index < showsByStation.length - 1 ? 'mb-16' : ''}>
          <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
            <Link
              to={`/station/${station.station_id}`}
              className="hover:opacity-70 transition-opacity"
            >
              <h2 className="text-sm tracking-wider uppercase mb-4">{station.name}</h2>
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {stationShows.map(show => (
              <ShowCard key={show.id} show={show} />
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}

