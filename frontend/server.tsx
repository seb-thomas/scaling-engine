import express from 'express'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import { createStaticHandler } from 'react-router-dom/server'
import handleRequest from './src/entry.server'
import { routes } from './src/routes'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const app = express()
const PORT = process.env.PORT || 3000
const API_URL = process.env.API_URL || 'http://localhost:8000'

// Serve static files
app.use('/assets', express.static(join(__dirname, '..', 'dist', 'assets')))
app.use(express.static(join(__dirname, '..', 'dist')))

// API proxy
app.use('/api', async (req, res) => {
  try {
    const url = `${API_URL}/api${req.path}${req.url.includes('?') ? req.url.substring(req.url.indexOf('?')) : ''}`
    const response = await fetch(url)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error(`API proxy error: ${response.status} ${response.statusText}`, errorText)
      res.status(response.status).json({ 
        error: 'API request failed',
        status: response.status,
        statusText: response.statusText,
        details: errorText
      })
      return
    }
    
    const data = await response.json()
    res.json(data)
  } catch (error) {
    console.error('API proxy error:', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    res.status(500).json({ 
      error: 'API request failed',
      details: errorMessage,
      stack: error instanceof Error ? error.stack : undefined
    })
  }
})

// Create static handler for React Router v7
const handler = createStaticHandler(routes)

// SSR handler - must be last to catch all routes
app.get('*', async (req, res) => {
  try {
    // Skip SSR for static assets that should be served directly
    if (req.path.startsWith('/assets/') || req.path.startsWith('/favicon')) {
      return res.status(404).send('Not found')
    }

    const request = new Request(`http://${req.get('host')}${req.url}`)
    const context = await handler.query(request)

    if (context instanceof Response) {
      throw context
    }

    const html = await handleRequest(
      request,
      context.statusCode || 200,
      new Headers(),
      context
    )

    res.setHeader('Content-Type', 'text/html')
    res.status(context.statusCode || 200)
    res.send(await html.text())
  } catch (error) {
    console.error('SSR Error for', req.url, ':', error)
    const errorMessage = error instanceof Error ? error.message : String(error)
    
    // Try to serve the HTML anyway so client-side routing can take over
    try {
      const htmlPath = join(__dirname, '..', 'index.html')
      const html = readFileSync(htmlPath, 'utf-8')
      res.setHeader('Content-Type', 'text/html')
      res.send(html)
    } catch (fallbackError) {
      res.status(500).send(`
        <html>
          <head><title>Server Error</title></head>
          <body>
            <h1>Server Error</h1>
            <p>${errorMessage}</p>
          </body>
        </html>
      `)
    }
  }
})

app.listen(PORT, () => {
  console.log(`🚀 SSR Server running on http://localhost:${PORT}`)
  console.log(`📡 API URL: ${API_URL}`)
})
