import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './components/ThemeProvider'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { AllBooksPage } from './pages/AllBooksPage'
import { AllShowsPage } from './pages/AllShowsPage'
import { StationPage } from './pages/StationPage'
import { ShowPage } from './pages/ShowPage'
import { BookDetailPage } from './pages/BookDetailPage'

export default function App() {
  return (
    <ThemeProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/books" element={<AllBooksPage />} />
          <Route path="/shows" element={<AllShowsPage />} />
          <Route path="/station/:stationId" element={<StationPage />} />
          <Route path="/show/:showId" element={<ShowPage />} />
          <Route path="/book/:bookId" element={<BookDetailPage />} />
        </Routes>
      </Layout>
    </ThemeProvider>
  )
}

