import express from 'express'
import { renderToString } from 'react-dom/server'
import { StaticRouter } from 'react-router-dom/server'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import React from 'react'
import App from './src/App'

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
    const data = await response.json()
    res.json(data)
  } catch (error) {
    console.error('API proxy error:', error)
    res.status(500).json({ error: 'API request failed' })
  }
})

// SSR handler
app.get('*', async (req, res) => {
  try {
    const htmlPath = join(__dirname, '..', 'index.html')
    const html = readFileSync(htmlPath, 'utf-8')
    
    const appHtml = renderToString(
      React.createElement(StaticRouter, { location: req.url },
        React.createElement(App)
      )
    )
    
    const finalHtml = html.replace(
      '<div id="root"></div>',
      `<div id="root">${appHtml}</div>`
    )
    
    res.send(finalHtml)
  } catch (error) {
    console.error('SSR Error:', error)
    res.status(500).send('Server Error')
  }
})

app.listen(PORT, () => {
  console.log(`🚀 SSR Server running on http://localhost:${PORT}`)
  console.log(`📡 API URL: ${API_URL}`)
})
