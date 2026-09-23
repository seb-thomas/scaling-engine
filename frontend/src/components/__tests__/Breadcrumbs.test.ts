import { describe, it, expect } from 'vitest'
import { render } from '@/test/render'
import Breadcrumbs from '../Breadcrumbs.astro'

const items = [
  { label: 'Home', href: '/' },
  { label: 'Shows', href: '/shows' },
  { label: 'Current Page' },
]

describe('Breadcrumbs', () => {
  it('renders breadcrumb items', async () => {
    const screen = await render(Breadcrumbs, { items })
    for (const label of ['Home', 'Shows', 'Current Page']) expect(screen.getByText(label)).toBeInTheDocument()
  })

  it('renders links for items with href', async () => {
    const screen = await render(Breadcrumbs, { items })
    expect(screen.getByText('Home').closest('a')).toHaveAttribute('href', '/')
    expect(screen.getByText('Shows').closest('a')).toHaveAttribute('href', '/shows')
  })

  it('renders span for items without href', async () => {
    const screen = await render(Breadcrumbs, { items })
    expect(screen.getByText('Current Page').tagName).toBe('SPAN')
  })
})
