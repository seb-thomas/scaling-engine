import express from 'express'
import { readFileSync, existsSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
// TODO: Update SSR to work with React Router v7 file-based routing
// For now, serving static files and falling back to client-side routing

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const app = express()
const PORT = process.env.PORT || 3000
const API_URL = process.env.API_URL || 'http://localhost:8000'

// Log startup info
console.log('🚀 Starting server...')
console.log('📁 __dirname:', __dirname)
console.log('📁 Process cwd:', process.cwd())

// React Router v7 builds to build/client/ instead of dist/
const buildDir = join(__dirname, '..', 'build', 'client')
const distDir = join(__dirname, '..', 'dist')
const staticDir = existsSync(buildDir) ? buildDir : distDir

console.log('📦 Static directory:', staticDir)
console.log('📦 Directory exists:', existsSync(staticDir))

// Serve static files from build/client (React Router v7) or dist (fallback)
if (existsSync(staticDir)) {
  app.use('/assets', express.static(join(staticDir, 'assets')))
  app.use(express.static(staticDir))
  console.log('✅ Static files configured from:', staticDir)
} else {
  console.error('❌ Static directory not found:', staticDir)
  console.error('   Tried buildDir:', buildDir, 'exists:', existsSync(buildDir))
  console.error('   Tried distDir:', distDir, 'exists:', existsSync(distDir))
}

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

// Serve HTML for all routes (client-side routing will handle it)
// TODO: Implement SSR with React Router v7 file-based routing using @react-router/node
app.get('*', (req, res) => {
  // Skip SSR for static assets
  if (req.path.startsWith('/assets/') || req.path.startsWith('/favicon')) {
    return res.status(404).send('Not found')
  }

  try {
    // Try multiple possible locations for index.html
    const possiblePaths = [
      join(staticDir, 'index.html'),  // React Router v7 build output
      join(__dirname, '..', 'index.html'),  // Root directory
      join(__dirname, '..', 'build', 'client', 'index.html'),  // Explicit build path
      join(__dirname, '..', 'dist', 'index.html'),  // Old dist path
    ]

    let htmlPath = null
    let html = null

    for (const path of possiblePaths) {
      if (existsSync(path)) {
        htmlPath = path
        html = readFileSync(path, 'utf-8')
        console.log('✅ Found index.html at:', path)
        break
      }
    }

    if (!html) {
      console.error('❌ index.html not found in any of these locations:')
      possiblePaths.forEach(p => console.error('   -', p, existsSync(p) ? '✅' : '❌'))
      
      return res.status(500).send(`
        <html>
          <head><title>Server Error</title></head>
          <body>
            <h1>Server Error</h1>
            <p>index.html not found</p>
            <p>Checked paths:</p>
            <ul>
              ${possiblePaths.map(p => `<li>${p} ${existsSync(p) ? '✅' : '❌'}</li>`).join('')}
            </ul>
            <p>Static dir: ${staticDir}</p>
            <p>__dirname: ${__dirname}</p>
          </body>
        </html>
      `)
    }

    res.setHeader('Content-Type', 'text/html')
    res.send(html)
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    const errorStack = error instanceof Error ? error.stack : undefined
    
    console.error('❌ Error serving HTML:', errorMessage)
    console.error('   Stack:', errorStack)
    console.error('   Request path:', req.path)
    console.error('   Request URL:', req.url)
    
    res.status(500).send(`
      <html>
        <head><title>Server Error</title></head>
        <body>
          <h1>Server Error</h1>
          <p>${errorMessage}</p>
          ${errorStack ? `<pre>${errorStack}</pre>` : ''}
        </body>
      </html>
    `)
  }
})

app.listen(PORT, () => {
  console.log(`🚀 SSR Server running on http://localhost:${PORT}`)
  console.log(`📡 API URL: ${API_URL}`)
  console.log(`📦 Static directory: ${staticDir}`)
  console.log(`📁 Working directory: ${process.cwd()}`)
})

// Error handling for uncaught errors
process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught Exception:', error)
  process.exit(1)
})

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Unhandled Rejection at:', promise, 'reason:', reason)
  process.exit(1)
})
