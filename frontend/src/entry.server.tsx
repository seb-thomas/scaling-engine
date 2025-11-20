import { renderToString } from 'react-dom/server'
import { createStaticRouter, StaticRouterProvider } from 'react-router-dom/server'
import { routes } from './routes'
import { readFileSync } from 'fs'
import { join } from 'path'
import { fileURLToPath } from 'url'
import { dirname } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

export default function handleRequest(
  request: Request,
  responseStatusCode: number,
  responseHeaders: Headers,
  routerContext: any
) {
  const router = createStaticRouter(routes, routerContext)
  const html = renderToString(<StaticRouterProvider router={router} context={routerContext} />)

  // Read the HTML template
  const htmlPath = join(__dirname, '..', '..', 'index.html')
  const template = readFileSync(htmlPath, 'utf-8')
  
  // Replace the root div with the rendered HTML
  const finalHtml = template.replace(
    '<div id="root"></div>',
    `<div id="root">${html}</div>`
  )

  responseHeaders.set('Content-Type', 'text/html')
  return new Response(finalHtml, {
    status: responseStatusCode,
    headers: responseHeaders,
  })
}

