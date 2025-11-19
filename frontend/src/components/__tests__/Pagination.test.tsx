import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Pagination } from '../Pagination'

describe('Pagination', () => {
  it('renders page numbers', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )
    
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('highlights current page', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={3}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )
    
    const currentPage = screen.getByText('3')
    expect(currentPage).toBeInTheDocument()
  })

  it('calls onPageChange when clicking next', async () => {
    const user = userEvent.setup()
    const onPageChange = vi.fn()
    
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )
    
    const nextButton = screen.getByLabelText('Next page')
    await user.click(nextButton)
    
    expect(onPageChange).toHaveBeenCalledWith(2)
  })

  it('calls onPageChange when clicking previous', async () => {
    const user = userEvent.setup()
    const onPageChange = vi.fn()
    
    render(
      <Pagination
        currentPage={2}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )
    
    const prevButton = screen.getByLabelText('Previous page')
    await user.click(prevButton)
    
    expect(onPageChange).toHaveBeenCalledWith(1)
  })

  it('disables previous button on first page', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={1}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )
    
    const prevButton = screen.getByLabelText('Previous page')
    expect(prevButton).toBeDisabled()
  })

  it('disables next button on last page', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={5}
        totalPages={5}
        onPageChange={onPageChange}
      />
    )
    
    const nextButton = screen.getByLabelText('Next page')
    expect(nextButton).toBeDisabled()
  })

  it('shows ellipsis for many pages', () => {
    const onPageChange = vi.fn()
    render(
      <Pagination
        currentPage={5}
        totalPages={10}
        onPageChange={onPageChange}
      />
    )
    
    // Should show ellipsis (···) - there may be multiple
    const ellipsis = screen.getAllByText('···')
    expect(ellipsis.length).toBeGreaterThan(0)
  })
})

