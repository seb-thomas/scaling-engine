import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BookCard } from '../BookCard'
import type { Book } from '@/types'

const mockBook: Book = {
  id: 1,
  title: 'Test Book',
  author: 'Test Author',
  description: 'A test book description',
  cover_image: 'https://example.com/cover.jpg',
  purchase_link: 'https://example.com/buy',
  episode: {
    id: 1,
    title: 'Test Episode',
    url: 'https://example.com/episode',
    aired_at: '2024-01-01T00:00:00Z',
    description: 'Episode description',
    brand: {
      id: 1,
      name: 'Test Show',
      station: {
        id: 1,
        name: 'Test Station',
        station_id: 'test',
      },
    },
  },
}

describe('BookCard', () => {
  it('renders book title', () => {
    render(<BookCard book={mockBook} />)
    expect(screen.getByText('Test Book')).toBeInTheDocument()
  })

  it('renders book author when provided', () => {
    render(<BookCard book={mockBook} />)
    expect(screen.getByText(/by Test Author/)).toBeInTheDocument()
  })

  it('renders show name', () => {
    render(<BookCard book={mockBook} />)
    expect(screen.getByText('Test Show')).toBeInTheDocument()
  })

  it('renders featured layout when featured prop is true', () => {
    render(
      <BrowserRouter>
        <BookCard book={mockBook} featured={true} />
      </BrowserRouter>
    )
    // Featured cards have larger title (text-3xl)
    const title = screen.getByText('Test Book')
    expect(title).toBeInTheDocument()
  })

  it('renders cover image when provided', () => {
    render(<BookCard book={mockBook} />)
    const image = screen.getByAltText(/Cover of Test Book/)
    expect(image).toBeInTheDocument()
    expect(image).toHaveAttribute('src', 'https://example.com/cover.jpg')
  })
})

