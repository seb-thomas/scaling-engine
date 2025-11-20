import Root from './root'
import { HomePage } from './pages/HomePage'
import { AllBooksPage } from './pages/AllBooksPage'
import { AllShowsPage } from './pages/AllShowsPage'
import { StationPage } from './pages/StationPage'
import { ShowPage } from './pages/ShowPage'
import { BookDetailPage } from './pages/BookDetailPage'
import type { RouteObject } from 'react-router-dom'

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Root />,
    children: [
      {
        index: true,
        element: <HomePage />,
        loader: HomePage.loader,
      },
      {
        path: 'books',
        element: <AllBooksPage />,
        loader: AllBooksPage.loader,
      },
      {
        path: 'shows',
        element: <AllShowsPage />,
        loader: AllShowsPage.loader,
      },
      {
        path: 'station/:stationId',
        element: <StationPage />,
        loader: StationPage.loader,
      },
      {
        path: 'show/:showId',
        element: <ShowPage />,
        loader: ShowPage.loader,
      },
      {
        path: 'book/:bookId',
        element: <BookDetailPage />,
        loader: BookDetailPage.loader,
      },
    ],
  },
]

