import { useState, useRef, useEffect } from 'react'
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
  const [loaded, setLoaded] = useState(false)
  const imgRef = useRef<HTMLImageElement>(null)

  // Handle images already loaded before hydration
  useEffect(() => {
    if (imgRef.current?.complete) setLoaded(true)
  }, [])

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
      ref={imgRef}
      src={src}
      alt={alt}
      className={`${className} ${loaded ? 'img-loaded' : 'img-loading'}`}
      onError={() => setHasError(true)}
      onLoad={() => setLoaded(true)}
      loading="lazy"
    />
  )
}
