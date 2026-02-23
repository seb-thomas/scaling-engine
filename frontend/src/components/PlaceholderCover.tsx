interface PlaceholderCoverProps {
  title: string
  author?: string
  brandColor?: string
  className?: string
}

const DEFAULT_TEXT_COLOR = '#d4c5a9'

/** Scale font size down for longer titles so text fits without truncation */
function titleFontSize(title: string): string {
  const len = title.length
  if (len <= 15) return 'clamp(0.6rem, 5cqi, 1.6rem)'
  if (len <= 25) return 'clamp(0.5rem, 4cqi, 1.4rem)'
  if (len <= 40) return 'clamp(0.45rem, 3.2cqi, 1.2rem)'
  return 'clamp(0.4rem, 2.6cqi, 1rem)'
}

export function PlaceholderCover({ title, author, brandColor, className }: PlaceholderCoverProps) {
  const textColor = brandColor || DEFAULT_TEXT_COLOR

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
      <div className="flex-1 flex flex-col justify-center px-[10%] py-2 overflow-hidden">
        <h3
          className="font-bold leading-[1.1] text-center"
          style={{
            fontFamily: "'EB Garamond', serif",
            fontSize: titleFontSize(title),
            color: textColor,
            overflowWrap: 'break-word',
            hyphens: 'auto',
          }}
          lang="en"
        >
          {title}
        </h3>
        {author && (
          <p
            className="text-neutral-400 text-center mt-[4%]"
            style={{
              fontSize: 'clamp(0.35rem, 2.2cqi, 0.7rem)',
              overflowWrap: 'break-word',
              hyphens: 'auto',
            }}
            lang="en"
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
