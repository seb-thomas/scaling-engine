import { StrictMode, startTransition } from 'react'
import { hydrateRoot } from 'react-dom/client'
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

startTransition(() => {
  hydrateRoot(
    document.getElementById('root')!,
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>
  )
})

