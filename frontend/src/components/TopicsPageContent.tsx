import { Breadcrumbs } from './Breadcrumbs'
import { TopicCard } from './TopicCard'
import type { Topic } from '../types'

interface TopicsPageContentProps {
  topics: Topic[]
  stationNames: string[]
}

export function TopicsPageContent({ topics, stationNames }: TopicsPageContentProps) {
  // Extract short network names: "BBC Radio 4" → "BBC", "NPR Fresh Air" → "NPR"
  const networks = [...new Set(stationNames.map(n => n.split(/\s/)[0]))]
  const stationsText = networks.length > 0
    ? networks.join(' and ')
    : 'radio'

  return (
    <div className="container py-12">
      <Breadcrumbs
        items={[
          { label: 'Home', href: '/' },
          { label: 'Topics' },
        ]}
      />

      <div className="mb-12">
        <h1 className="text-2xl font-medium mb-4">Browse by Topic</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Explore books discussed on radio by genre and theme. Each topic brings together
          thoughtfully curated conversations from {stationsText} programs.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
        {topics.map((topic) => (
          <TopicCard key={topic.slug} topic={topic} />
        ))}
      </div>
    </div>
  )
}
