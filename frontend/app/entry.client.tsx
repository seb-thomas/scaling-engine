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

// Check for duplication before hydration
const hasDuplication = rootElement.children.length > 1

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

startTransition(() => {
  if (hasDuplication) {
    // Duplication already exists - clear and render fresh
    fixDuplication()
  } else {
    // Normal case - try to hydrate server-rendered content
    const hasServerContent = rootElement.children.length > 0
    if (hasServerContent) {
      try {
        hydrateRoot(rootElement, app)
        // CRITICAL: Check for duplication AFTER hydration completes
        // React may append instead of replace during failed hydration
        requestAnimationFrame(() => {
          if (!fixDuplication()) {
            // Also check after a short delay in case hydration is async
            setTimeout(() => {
              fixDuplication()
            }, 100)
          }
        })
      } catch (error) {
        // If hydration fails, clear and render fresh
        console.error('Hydration failed, rendering fresh:', error)
        rootElement.innerHTML = ''
        createRoot(rootElement).render(app)
      }
    } else {
      // No server content, render fresh (SPA mode)
      createRoot(rootElement).render(app)
    }
  }
})

