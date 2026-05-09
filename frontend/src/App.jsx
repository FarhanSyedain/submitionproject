import { Route, Routes, useLocation } from 'react-router-dom'

import Sidebar from './components/Sidebar.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import LandingPage from './pages/LandingPage.jsx'
import NewAnalysisPage from './pages/NewAnalysisPage.jsx'
import SessionPage from './pages/SessionPage.jsx'

export default function App() {
  const { pathname } = useLocation()
  const isLanding = pathname === '/'
  const showSidebar = !isLanding

  return (
    <div className="flex min-h-screen">
      {showSidebar && <Sidebar />}
      <main className={isLanding ? 'flex-1' : 'flex-1 px-6 py-8 md:px-10'}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/dashboard"
            element={
              <PageContainer>
                <DashboardPage />
              </PageContainer>
            }
          />
          <Route
            path="/analyze/new"
            element={
              <PageContainer>
                <NewAnalysisPage />
              </PageContainer>
            }
          />
          <Route
            path="/analysis/:id"
            element={
              <PageContainer>
                <SessionPage />
              </PageContainer>
            }
          />
          <Route
            path="*"
            element={
              <PageContainer>
                <NotFound />
              </PageContainer>
            }
          />
        </Routes>
      </main>
    </div>
  )
}

function PageContainer({ children }) {
  // Top padding gets a bit extra so the page doesn't sit flush under the
  // implicit nav baseline; bottom padding gives breathing room to footers.
  return <div className="mx-auto max-w-6xl px-2 pt-2 pb-16">{children}</div>
}

function NotFound() {
  return (
    <div className="glass-card text-sm muted">
      Page not found — try the{' '}
      <a href="/dashboard" className="underline" style={{ color: 'var(--text-accent)' }}>
        dashboard
      </a>
      .
    </div>
  )
}
