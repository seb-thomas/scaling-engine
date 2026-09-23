import { describe, it, expect } from 'vitest'
import { within } from '@testing-library/dom'
import { render } from '@/test/render'
import Header from '../Header.astro'

describe('Header', () => {
  it('labels the mobile menu button and starts closed', async () => {
    const screen = await render(Header, { pathname: '/' })
    const button = screen.getByRole('button', { name: 'Open menu' })
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(document.getElementById('mobile-nav')).toHaveClass('hidden')
  })

  it('highlights the active section', async () => {
    await render(Header, { pathname: '/show/front-row' })
    const desktopNav = document.querySelectorAll('nav')[0] as HTMLElement
    expect(within(desktopNav).getByText('Shows')).toHaveClass('text-gray-900')
    expect(within(desktopNav).getByText('Latest')).toHaveClass('text-gray-600')
  })
})
