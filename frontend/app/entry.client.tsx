import { StrictMode, startTransition } from 'react'
import { hydrateRoot, createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import Root from './root'
import HomePage, { loader as homePageLoader } from './routes/_index'
import AllBooksPage, { loader as allBooksPageLoader } from './routes/books'
import AllShowsPage, { loader as allShowsPageLoader } from './routes/shows'
import StationPage, { loader as stationPageLoader } from './routes/station.$stationId'
import ShowPage, { loader as showPageLoader } from './routes/show.$showId'
import BookDetailPage, { loader as bookDetailPageLoader } from './routes/book.$bookId'

// Create router with file-based routes
const router = createBrowserRouter([
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
])

const rootElement = document.getElementById('root')!

// AGGRESSIVE: Check for duplication immediately and continuously
// This must run BEFORE React tries to hydrate to prevent appending
const checkDuplication = () => {
  return rootElement.children.length > 1
}

// Check immediately before any React code runs
if (checkDuplication()) {
  console.warn('⚠️ Duplication detected BEFORE React load! Clearing immediately')
  rootElement.innerHTML = ''
}

const app = (
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
)

// Function to fix duplication by clearing and re-rendering
const fixDuplication = () => {
  if (rootElement.children.length > 1) {
    console.warn('⚠️ Duplication detected! Clearing and re-rendering')
    rootElement.innerHTML = ''
    createRoot(rootElement).render(app)
    return true
  }
  return false
}

// Set up continuous monitoring for duplication
const monitorDuplication = () => {
  // Check immediately
  if (fixDuplication()) return
  
  // Check after next frame
  requestAnimationFrame(() => {
    if (fixDuplication()) return
    
    // Check after a short delay
    setTimeout(() => {
      if (fixDuplication()) return
      
      // Final check after React has had time to hydrate
      setTimeout(() => {
        fixDuplication()
      }, 500)
    }, 100)
  })
}

startTransition(() => {
  // WORKAROUND for React Router SSR hydration bug (https://github.com/remix-run/react-router/issues/10918)
  // Skip hydration entirely and always render fresh to prevent double-rendering
  // The server-rendered HTML is still useful for SEO and initial load performance
  console.log('Rendering fresh (hydration disabled to prevent double-render bug)')
  rootElement.innerHTML = ''
  createRoot(rootElement).render(app)
})

