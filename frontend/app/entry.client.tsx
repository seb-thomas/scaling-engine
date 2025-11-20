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

// If root already has multiple children (duplication), clear it first
if (rootElement.children.length > 1) {
  console.warn('⚠️ Detected duplicate content in root, clearing before hydration')
  rootElement.innerHTML = ''
}

const app = (
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>
)

// Check if root has server-rendered content (from SSR)
const hasServerContent = rootElement.children.length > 0

startTransition(() => {
  if (hasServerContent) {
    // Hydrate existing server-rendered content
    try {
      hydrateRoot(rootElement, app)
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
})

