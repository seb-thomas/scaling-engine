import { afterEach } from 'vitest'
import { JSDOM } from 'jsdom'
import '@testing-library/jest-dom/vitest'

// Components render on the server (node environment, which Astro's compiler
// needs); a jsdom document is attached only for querying the resulting HTML.
const dom = new JSDOM('<!doctype html><html><body></body></html>')
Object.assign(globalThis, {
  window: dom.window,
  document: dom.window.document,
  Event: dom.window.Event,
  HTMLElement: dom.window.HTMLElement,
  Element: dom.window.Element,
  Node: dom.window.Node,
  getComputedStyle: dom.window.getComputedStyle,
})

afterEach(() => {
  document.body.innerHTML = ''
})
