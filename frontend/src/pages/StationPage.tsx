import { useLoaderData } from 'react-router-dom'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { ShowCard } from '@/components/ShowCard'
import { fetchStation, fetchStationShows } from '@/api/client'
import type { Station, Show } from '@/types'

export async function loader({ params }: { params: { stationId: string } }) {
  const { stationId } = params
  if (!stationId) {
    throw new Response('Station not found', { status: 404 })
  }

  const [stationData, showsData] = await Promise.all([
    fetchStation(stationId),
    fetchStationShows(stationId).catch(() => [])
  ])

  const station = Array.isArray(stationData) ? stationData[0] : stationData
  if (!station) {
    throw new Response('Station not found', { status: 404 })
  }

  const shows = Array.isArray(showsData) 
    ? showsData 
    : showsData.results || []

  return { station, shows }
}

export function StationPage() {
  const { station, shows } = useLoaderData<typeof loader>()

  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    { label: station.name }
  ]

  return (
    <div className="container mx-auto px-4 py-12">
      <Breadcrumbs items={breadcrumbItems} />

      <div className="mb-12">
        <h1 className="text-4xl mb-4" style={{ fontFamily: "'EB Garamond', serif" }}>
          {station.name}
        </h1>
        {station.url && (
          <p className="text-xl text-gray-600 dark:text-gray-400 mb-2">
            <a href={station.url} target="_blank" rel="noopener" className="hover:opacity-70 transition-opacity">
              Visit {station.name}
            </a>
          </p>
        )}
        <p className="text-sm text-gray-500 dark:text-gray-500">
          {shows.length} show{shows.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div>
        <div className="border-b border-gray-200 dark:border-gray-800 mb-8">
          <h2 className="text-sm tracking-wider uppercase mb-4">Shows</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {shows.map(show => (
            <ShowCard key={show.id} show={show} />
          ))}
        </div>
      </div>
    </div>
  )
}

