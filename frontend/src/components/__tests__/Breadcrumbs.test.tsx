import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Breadcrumbs } from '../Breadcrumbs'

describe('Breadcrumbs', () => {
  it('renders breadcrumb items', () => {
    const items = [
      { label: 'Home', href: '/' },
      { label: 'Shows', href: '/shows' },
      { label: 'Current Page' },
    ]

    render(<Breadcrumbs items={items} />)

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Shows')).toBeInTheDocument()
    expect(screen.getByText('Current Page')).toBeInTheDocument()
  })

  it('renders links for items with href', () => {
    const items = [
      { label: 'Home', href: '/' },
      { label: 'Current' },
    ]

    render(<Breadcrumbs items={items} />)

    const homeLink = screen.getByText('Home')
    expect(homeLink.closest('a')).toHaveAttribute('href', '/')
  })

  it('renders span for items without href', () => {
    const items = [
      { label: 'Home', href: '/' },
      { label: 'Current' },
    ]

    render(<Breadcrumbs items={items} />)

    const current = screen.getByText('Current')
    expect(current.tagName).toBe('SPAN')
  })
})

