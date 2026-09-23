import { describe, it, expect } from 'vitest'
import { render } from '@/test/render'
import Pagination from '../Pagination.astro'

const url = (path: string) => new URL(path, 'https://radioreads.fun')

describe('Pagination', () => {
  it('renders page numbers as links', async () => {
    const screen = await render(Pagination, { currentPage: 1, totalPages: 5, url: url('/books') })
    expect(screen.getByRole('link', { name: '1' })).toHaveAttribute('href', '/books')
    expect(screen.getByRole('link', { name: '5' })).toHaveAttribute('href', '/books?page=5')
  })

  it('marks the current page', async () => {
    const screen = await render(Pagination, { currentPage: 3, totalPages: 5, url: url('/books?page=3') })
    expect(screen.getByRole('link', { name: '3' })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('link', { name: '2' })).not.toHaveAttribute('aria-current')
  })

  it('links next and previous pages', async () => {
    const screen = await render(Pagination, { currentPage: 3, totalPages: 5, url: url('/books?page=3') })
    expect(screen.getByLabelText('Next page')).toHaveAttribute('href', '/books?page=4')
    expect(screen.getByLabelText('Previous page')).toHaveAttribute('href', '/books?page=2')
  })

  it('keeps other query params such as search', async () => {
    const screen = await render(Pagination, { currentPage: 1, totalPages: 3, url: url('/books?search=woolf') })
    expect(screen.getByLabelText('Next page')).toHaveAttribute('href', '/books?search=woolf&page=2')
  })

  it('disables previous on the first page', async () => {
    const screen = await render(Pagination, { currentPage: 1, totalPages: 5, url: url('/books') })
    const prev = screen.getByLabelText('Previous page')
    expect(prev.tagName).toBe('SPAN')
    expect(prev).toHaveAttribute('aria-disabled', 'true')
  })

  it('disables next on the last page', async () => {
    const screen = await render(Pagination, { currentPage: 5, totalPages: 5, url: url('/books?page=5') })
    expect(screen.getByLabelText('Next page')).toHaveAttribute('aria-disabled', 'true')
  })

  it('shows ellipsis for many pages', async () => {
    const screen = await render(Pagination, { currentPage: 1, totalPages: 20, url: url('/books') })
    expect(screen.getByText('···')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '20' })).toBeInTheDocument()
  })
})
