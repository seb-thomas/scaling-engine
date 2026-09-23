import { describe, it, expect } from 'vitest'
import { render } from '@/test/render'
import AffiliateDisclosure from '../AffiliateDisclosure.astro'

describe('AffiliateDisclosure', () => {
  it('renders disclosure text', async () => {
    const screen = await render(AffiliateDisclosure)
    expect(screen.getByText(/As an affiliate of Bookshop.org/)).toBeInTheDocument()
  })
})
