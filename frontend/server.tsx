import React from 'react'
import { createStaticHandler } from 'react-router'
import { renderToString } from 'react-dom/server'
import { readFileSync, existsSync } from 'fs'
import { join } from 'path'
import Root from './app/root'
import HomePage, { loader as homePageLoader } from './app/routes/_index'
import AllBooksPage, { loader as allBooksPageLoader } from './app/routes/books'
import AllShowsPage, { loader as allShowsPageLoader } from './app/routes/shows'
import StationPage, { loader as stationPageLoader } from './app/routes/station.$stationId'
import ShowPage, { loader as showPageLoader } from './app/routes/show.$showId'
import BookDetailPage, { loader as bookDetailPageLoader } from './app/routes/book.$bookId'
import { RouterProvider, createStaticRouter } from 'react-router'

const PORT = parseInt(process.env.PORT || '3000', 10)
const API_URL = process.env.API_URL || 'http://localhost:8000'

// Get directory paths - Bun uses import.meta.dir
const __dirname = import.meta.dir || process.cwd()
const buildDir = join(__dirname, 'build', 'client')
const distDir = join(__dirname, 'dist')
const staticDir = existsSync(buildDir) ? buildDir : distDir

console.log('🚀 Starting Bun server...')
console.log('📁 __dirname:', __dirname)
console.log('📁 Process cwd:', process.cwd())
console.log('📦 Static directory:', staticDir)
console.log('📦 Directory exists:', existsSync(staticDir))

// Define routes for SSR (matching entry.client.tsx)
const routes = [
  {
    path: '/',
    element: <Root />,
    children: [
      {
        index: true,
        element: <HomePage />,
        loader: homePageLoader,
      },
      {
        path: 'books',
        element: <AllBooksPage />,
        loader: allBooksPageLoader,
      },
      {
        path: 'shows',
        element: <AllShowsPage />,
        loader: allShowsPageLoader,
      },
      {
        path: 'station/:stationId',
        element: <StationPage />,
        loader: stationPageLoader,
      },
      {
        path: 'show/:showId',
        element: <ShowPage />,
        loader: showPageLoader,
      },
      {
        path: 'book/:bookId',
        element: <BookDetailPage />,
        loader: bookDetailPageLoader,
      },
    ],
  },
]

// Create static handler for SSR
const handler = createStaticHandler(routes)

// Helper to serve static files
async function serveStaticFile(filePath: string): Promise<Response | null> {
  try {
    if (!existsSync(filePath)) {
      return null
    }

    const file = Bun.file(filePath)
    if (!(await file.exists())) {
      return null
    }

    // Determine content type
    const ext = filePath.split('.').pop()?.toLowerCase()
    const contentTypes: Record<string, string> = {
      html: 'text/html',
      css: 'text/css',
      js: 'application/javascript',
      json: 'application/json',
      png: 'image/png',
      jpg: 'image/jpeg',
      jpeg: 'image/jpeg',
      svg: 'image/svg+xml',
      ico: 'image/x-icon',
      woff: 'font/woff',
      woff2: 'font/woff2',
    }

    const contentType = contentTypes[ext || ''] || 'application/octet-stream'

    return new Response(file, {
      headers: {
        'Content-Type': contentType,
      },
    })
  } catch (error) {
    console.error('Error serving static file:', error)
    return null
  }
}

// Helper to transform HTML (replace entry.client.tsx with built asset)
function transformHTML(html: string): string {
  try {
    const manifestPath = join(staticDir, '.vite', 'manifest.json')
    if (existsSync(manifestPath)) {
      const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'))
      const entryClient = manifest['app/entry.client.tsx']
      if (entryClient && entryClient.file) {
        html = html.replace(
          'src="/app/entry.client.tsx"',
          `src="/${entryClient.file}"`
        )
        console.log('✅ Transformed HTML: replaced entry.client.tsx with', entryClient.file)
      }
    }
  } catch (error) {
    console.warn('⚠️ Error transforming HTML:', error)
  }
  return html
}

// Start Bun server
Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url)
    const pathname = url.pathname

    // Handle static assets
    if (pathname.startsWith('/assets/') || pathname.startsWith('/favicon')) {
      const filePath = join(staticDir, pathname)
      const response = await serveStaticFile(filePath)
      if (response) {
        return response
      }
      return new Response('Not found', { status: 404 })
    }

    // Handle API proxy
    if (pathname.startsWith('/api/')) {
      try {
        const apiPath = pathname.replace('/api', '')
        const queryString = url.search
        const apiUrl = `${API_URL}/api${apiPath}${queryString}`
        
        const response = await fetch(apiUrl, {
          method: req.method,
          headers: {
            'Content-Type': 'application/json',
          },
          body: req.method !== 'GET' && req.method !== 'HEAD' ? await req.text() : undefined,
        })

        if (!response.ok) {
          const errorText = await response.text()
          console.error(`API proxy error: ${response.status} ${response.statusText}`, errorText)
          return new Response(
            JSON.stringify({
              error: 'API request failed',
              status: response.status,
              statusText: response.statusText,
              details: errorText,
            }),
            {
              status: response.status,
              headers: { 'Content-Type': 'application/json' },
            }
          )
        }

        const data = await response.json()
        return new Response(JSON.stringify(data), {
          headers: { 'Content-Type': 'application/json' },
        })
      } catch (error) {
        console.error('API proxy error:', error)
        const errorMessage = error instanceof Error ? error.message : String(error)
        return new Response(
          JSON.stringify({
            error: 'API request failed',
            details: errorMessage,
          }),
          {
            status: 500,
            headers: { 'Content-Type': 'application/json' },
          }
        )
      }
    }

    // Handle SSR with React Router
    try {
      // Create a context from the request
      const context = await handler.query(req)
      
      // Create static router with the context
      const router = createStaticRouter(handler.dataRoutes, context)
      
      // Load index.html template
      const possiblePaths = [
        join(staticDir, 'index.html'),
        join(__dirname, 'index.html'),
        join(__dirname, 'build', 'client', 'index.html'),
        join(__dirname, 'dist', 'index.html'),
      ]
      
      let htmlTemplate = null
      for (const path of possiblePaths) {
        if (existsSync(path)) {
          htmlTemplate = readFileSync(path, 'utf-8')
          break
        }
      }
      
      if (!htmlTemplate) {
        throw new Error('index.html not found')
      }
      
      // Render React app to string
      const renderedHTML = renderToString(
        <RouterProvider router={router} context={context} />
      )
      
      // Replace the root div with rendered content
      const finalHTML = htmlTemplate.replace(
        '<div id="root"></div>',
        `<div id="root">${renderedHTML}</div>`
      )
      
      // Transform HTML to fix entry.client.tsx path
      const transformedHTML = transformHTML(finalHTML)
      
      return new Response(transformedHTML, {
        headers: { 'Content-Type': 'text/html' },
      })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      const errorStack = error instanceof Error ? error.stack : undefined

      console.error('❌ Error handling request:', errorMessage)
      console.error('   Stack:', errorStack)
      console.error('   Path:', pathname)

      return new Response(
        `
        <html>
          <head><title>Server Error</title></head>
          <body>
            <h1>Server Error</h1>
            <p>${errorMessage}</p>
            ${errorStack ? `<pre>${errorStack}</pre>` : ''}
          </body>
        </html>
      `,
        {
          status: 500,
          headers: { 'Content-Type': 'text/html' },
        }
      )
    }
  },
})

console.log(`🚀 Bun SSR Server running on http://localhost:${PORT}`)
console.log(`📡 API URL: ${API_URL}`)
console.log(`📦 Static directory: ${staticDir}`)
console.log(`📁 Working directory: ${process.cwd()}`)

// Error handling
process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error)
  process.exit(1)
})

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason)
  process.exit(1)
})
