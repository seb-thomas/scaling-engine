import { Outlet } from 'react-router-dom'
import { ThemeProvider } from '../src/components/ThemeProvider'
import { Layout } from '../src/components/Layout'
import '../src/index.css'

export default function Root() {
  return (
    <ThemeProvider>
      <Layout>
        <Outlet />
      </Layout>
    </ThemeProvider>
  )
}

