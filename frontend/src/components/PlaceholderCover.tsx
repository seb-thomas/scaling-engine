interface PlaceholderCoverProps {
  title: string
  author?: string
  brandColor?: string
  className?: string
}

const DEFAULT_COLOR = '#1a1a2e'

export function PlaceholderCover({ title, author, brandColor, className }: PlaceholderCoverProps) {
  const bgColor = brandColor || DEFAULT_COLOR

  return (
    <div
      className={`relative overflow-hidden flex flex-col justify-between ${className}`}
      style={{
        backgroundColor: bgColor,
        aspectRatio: '2 / 3',
      }}
    >
      {/* Decorative top line */}
      <div
        className="mx-4 mt-6 h-px opacity-40"
        style={{ backgroundColor: '#fff' }}
      />

      {/* Title and author */}
      <div className="flex-1 flex flex-col justify-center px-4 py-3">
        <h3
          className="text-white font-bold leading-tight text-center break-words"
          style={{
            fontFamily: "'EB Garamond', serif",
            fontSize: 'clamp(0.7rem, 4cqi, 1.4rem)',
            textShadow: '0 1px 3px rgba(0,0,0,0.3)',
          }}
        >
          {title}
        </h3>
        {author && (
          <p
            className="text-white/70 text-center mt-2 break-words"
            style={{
              fontSize: 'clamp(0.5rem, 2.5cqi, 0.8rem)',
            }}
          >
            {author}
          </p>
        )}
      </div>

      {/* Decorative bottom line */}
      <div
        className="mx-4 mb-6 h-px opacity-40"
        style={{ backgroundColor: '#fff' }}
      />
    </div>
  )
}
