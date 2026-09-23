import { describe, it, expect } from 'vitest'
import { render } from '@/test/render'
import ImageWithFallback from '../ImageWithFallback.astro'

describe('ImageWithFallback', () => {
  it('renders the image with a hidden placeholder for load errors', async () => {
    const screen = await render(ImageWithFallback, { src: '/c.jpg', alt: 'Cover of X', title: 'X' })
    const img = screen.getByAltText('Cover of X')
    const placeholder = img.nextElementSibling
    expect(placeholder).toHaveAttribute('role', 'img')
    expect(placeholder).toHaveClass('hidden')
  })

  it('swaps to the placeholder when the image fails', async () => {
    const screen = await render(ImageWithFallback, { src: '/c.jpg', alt: 'Cover of X', title: 'X' })
    const img = screen.getByAltText('Cover of X')
    // jsdom doesn't run inline handlers, so invoke the onerror attribute directly
    new Function(img.getAttribute('onerror')!).call(img)
    expect(img.style.display).toBe('none')
    expect(img.nextElementSibling?.classList.contains('hidden')).toBe(false)
  })

  it('renders only the placeholder when there is no src', async () => {
    const screen = await render(ImageWithFallback, { alt: 'Cover of X', title: 'X', author: 'Y' })
    expect(document.querySelector('img')).toBeNull()
    expect(screen.getByRole('img', { name: 'Cover of X' })).not.toHaveClass('hidden')
    expect(screen.getByText('Y')).toBeInTheDocument()
  })

  it('loads eagerly at high priority when priority is set', async () => {
    const screen = await render(ImageWithFallback, { src: '/c.jpg', alt: 'A', priority: true })
    const img = screen.getByAltText('A')
    expect(img).toHaveAttribute('loading', 'eager')
    expect(img).toHaveAttribute('fetchpriority', 'high')
  })
})
