import { useState } from 'react'
import { PlaceholderCover } from './PlaceholderCover'

interface ImageWithFallbackProps {
  src?: string
  alt: string
  className?: string
  title?: string
  author?: string
  brandColor?: string
  /** Above-the-fold image (e.g. the LCP cover): load eagerly at high priority */
  priority?: boolean
}

export function ImageWithFallback({ src, alt, className, title, author, brandColor, priority = false }: ImageWithFallbackProps) {
  const [hasError, setHasError] = useState(false)

  if (!src || hasError) {
    if (title) {
      return <PlaceholderCover title={title} author={author} brandColor={brandColor} className={className} />
    }
    return (
      <div className={`bg-gray-200 dark:bg-gray-800 flex items-center justify-center ${className}`} style={{ aspectRatio: '2 / 3' }}>
        <span className="text-gray-400 text-sm">No Cover</span>
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => setHasError(true)}
      // Nominal 2:3 cover size so the browser reserves space before load;
      // the h-auto classes keep the real aspect ratio once it arrives
      width={400}
      height={600}
      loading={priority ? 'eager' : 'lazy'}
      // React 18 only passes fetchpriority through in lowercase
      {...(priority ? { fetchpriority: 'high' } : {})}
    />
  )
}
