import { ArrowRight } from 'lucide-react'
import type { Topic } from '@/types'

type TopicCardProps = {
  topic: Topic
}

const TOPIC_COLORS: Record<string, string> = {
  fiction: '#2d5986',
  classics: '#8b4513',
  'prize-winners': '#6b4c8a',
  debut: '#c2703e',
  history: '#5a6b7c',
  biography: '#4a7c59',
  cookbooks: '#7c4a4a',
  politics: '#3d5a80',
  science: '#4a6b7c',
  arts: '#8a6b4c',
}

export function TopicCard({ topic }: TopicCardProps) {
  const color = TOPIC_COLORS[topic.slug] || '#6b6b6b'

  const wavePattern = (c: string) =>
    `data:image/svg+xml,%3Csvg width='32' height='24' viewBox='0 0 32 24' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M2 6 Q 4 4, 6 6 T 10 6 T 14 6 T 18 6 T 22 6 T 26 6 T 30 6' stroke='${encodeURIComponent(c)}' stroke-width='1.5' fill='none'/%3E%3Cpath d='M2 12 Q 4 10, 6 12 T 10 12 T 14 12 T 18 12 T 22 12 T 26 12 T 30 12' stroke='${encodeURIComponent(c)}' stroke-width='1.5' fill='none'/%3E%3Cpath d='M2 18 Q 4 16, 6 18 T 10 18 T 14 18 T 18 18 T 22 18 T 26 18 T 30 18' stroke='${encodeURIComponent(c)}' stroke-width='1.5' fill='none'/%3E%3C/svg%3E`

  return (
    <article className="group block">
      <a href={`/topic/${topic.slug}`} className="block">
        {/* Wave pattern masthead */}
        <div className="mb-4 overflow-hidden h-6">
          <div
            className="h-6"
            style={{
              backgroundImage: `url("${wavePattern(color)}")`,
              backgroundRepeat: 'repeat',
              backgroundSize: '32px 24px',
            }}
          />
        </div>

        {/* Content */}
        <div>
          <h3
            className="font-serif text-xl mb-2 group-hover:text-orange-900 dark:group-hover:text-orange-100 transition-colors leading-tight"
          >
            {topic.name}
          </h3>
          {topic.description && (
            <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-3 line-clamp-2">
              {topic.description}
            </p>
          )}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600 dark:text-gray-400 group-hover:text-orange-800 dark:group-hover:text-orange-300 transition-colors">
              {topic.book_count.toLocaleString()} {topic.book_count === 1 ? 'book' : 'books'}
            </div>
            <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-orange-700 dark:group-hover:text-orange-400 group-hover:translate-x-2 transition-all" />
          </div>
        </div>
      </a>
    </article>
  )
}
