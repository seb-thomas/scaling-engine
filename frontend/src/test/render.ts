import { experimental_AstroContainer as AstroContainer } from 'astro/container'
import { within } from '@testing-library/dom'

/** Server-render an Astro component into document.body; returns queries bound to it */
export async function render(Component: any, props: Record<string, unknown> = {}) {
  const container = await AstroContainer.create()
  document.body.innerHTML = await container.renderToString(Component, { props })
  return within(document.body)
}
