interface PlaceholderCoverProps {
  title: string
  author?: string
  brandColor?: string
  className?: string
}

const DEFAULT_TEXT_COLOR = '#c8553d'

/** Truncate title at last word boundary to avoid orphaned letters */
function truncateTitle(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text
  const truncated = text.slice(0, maxChars)
  const lastSpace = truncated.lastIndexOf(' ')
  if (lastSpace < maxChars * 0.4) return truncated.trimEnd()
  return truncated.slice(0, lastSpace).trimEnd()
}

export function PlaceholderCover({ title, author, brandColor, className }: PlaceholderCoverProps) {
  const textColor = brandColor || DEFAULT_TEXT_COLOR
  const displayTitle = truncateTitle(title, 30)

  return (
    <div
      className={`relative overflow-hidden flex flex-col justify-between bg-neutral-900 ${className}`}
      style={{ aspectRatio: '2 / 3' }}
    >
      {/* Decorative top line */}
      <div
        className="mx-[12%] mt-[12%] h-px opacity-30"
        style={{ backgroundColor: textColor }}
      />

      {/* Title and author */}
      <div className="flex-1 flex flex-col justify-center px-[12%] py-2 overflow-hidden">
        <h3
          className="font-bold leading-[1.1] text-center break-words"
          style={{
            fontFamily: "'EB Garamond', serif",
            fontSize: 'clamp(0.55rem, 4.5cqi, 1.5rem)',
            color: textColor,
          }}
        >
          {displayTitle}
        </h3>
        {author && (
          <p
            className="text-neutral-400 text-center mt-[4%] break-words"
            style={{
              fontSize: 'clamp(0.4rem, 2.5cqi, 0.75rem)',
            }}
          >
            {author}
          </p>
        )}
      </div>

      {/* Decorative bottom line */}
      <div
        className="mx-[12%] mb-[12%] h-px opacity-30"
        style={{ backgroundColor: textColor }}
      />
    </div>
  )
}
