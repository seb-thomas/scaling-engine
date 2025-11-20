import { Outlet } from 'react-router'
import { ThemeProvider } from './components/ThemeProvider'
import { Layout } from './components/Layout'
import './index.css'

export default function Root() {
  return (
    <ThemeProvider>
      <Layout>
        <Outlet />
      </Layout>
    </ThemeProvider>
  )
}

