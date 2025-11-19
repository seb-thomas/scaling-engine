import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AffiliateDisclosure } from '../AffiliateDisclosure'

describe('AffiliateDisclosure', () => {
  it('renders disclosure text', () => {
    render(<AffiliateDisclosure />)
    
    expect(
      screen.getByText(/As an affiliate of Bookshop.org/)
    ).toBeInTheDocument()
    expect(
      screen.getByText(/we earn from qualifying purchases/)
    ).toBeInTheDocument()
  })
})

