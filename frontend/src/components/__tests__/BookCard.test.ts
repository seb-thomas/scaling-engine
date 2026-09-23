import { describe, it, expect } from 'vitest'
import { render } from '@/test/render'
import { mockBook } from '@/test/fixtures'
import BookCard from '../BookCard.astro'

describe('BookCard', () => {
  it('renders book title', async () => {
    const screen = await render(BookCard, { book: mockBook })
    expect(screen.getByRole('heading', { name: 'Test Book' })).toBeInTheDocument()
  })

  it('renders book author when provided', async () => {
    const screen = await render(BookCard, { book: mockBook })
    expect(screen.getByText(/by Test Author/)).toBeInTheDocument()
  })

  it('renders station, show and date in metadata', async () => {
    const screen = await render(BookCard, { book: mockBook })
    expect(screen.getByText('Test Show · Test Station · Jan 1, 2024')).toBeInTheDocument()
  })

  it('links to the book under its show', async () => {
    const screen = await render(BookCard, { book: mockBook })
    expect(screen.getByRole('link')).toHaveAttribute('href', '/test-show/test-book')
  })

  it('renders featured layout with description and long date', async () => {
    const screen = await render(BookCard, { book: mockBook, featured: true })
    expect(screen.getByText('A test book description')).toBeInTheDocument()
    expect(screen.getByText('Heard on Test Show, Test Station · January 1, 2024')).toBeInTheDocument()
  })

  it('renders a lazy cover image with intrinsic size', async () => {
    const screen = await render(BookCard, { book: mockBook })
    const image = screen.getByAltText(/Cover of Test Book/)
    expect(image).toHaveAttribute('src', 'https://example.com/cover.jpg')
    expect(image).toHaveAttribute('loading', 'lazy')
    expect(image).toHaveAttribute('width', '400')
    expect(image).toHaveAttribute('height', '600')
  })

  it('uses h2 for the title so headings do not skip a level', async () => {
    const screen = await render(BookCard, { book: mockBook })
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Test Book')
  })
})
