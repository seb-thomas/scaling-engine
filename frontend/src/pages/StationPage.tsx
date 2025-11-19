import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { ShowCard } from '@/components/ShowCard'
import { fetchStation, fetchStationShows } from '@/api/client'
import type { Station, Show } from '@/types'

export function StationPage() {
  const { stationId } = useParams<{ stationId: string }>()
  const [station, setStation] = useState<Station | null>(null)
  const [shows, setShows] = useState<Show[]>([])

  useEffect(() => {
    if (!stationId) return
    
    fetchStation(stationId).then(data => {
      if (Array.isArray(data)) {
        setStation(data[0] || null)
      } else {
        setStation(data)
      }
    }).catch(console.error)

    fetchStationShows(stationId).then(data => {
      if (Array.isArray(data)) {
        setShows(data)
      } else if (data.results) {
        setShows(data.results)
      }
    }).catch(console.error)
  }, [stationId])

  if (!station) {
    return (
      <div className="container mx-auto px-4 py-12">
        <p>Station not found</p>
      </div>
    )
  }

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

