import { useState } from 'react'
import { PlaceholderCover } from './PlaceholderCover'

interface ImageWithFallbackProps {
  src?: string
  alt: string
  className?: string
  title?: string
  author?: string
  brandColor?: string
}

export function ImageWithFallback({ src, alt, className, title, author, brandColor }: ImageWithFallbackProps) {
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
      loading="lazy"
    />
  )
}
