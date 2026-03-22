import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import EmailReviewPage from './pages/EmailReviewPage'
import ReceiptTrackerPage from './pages/ReceiptTrackerPage'
import SettingsPage from './pages/SettingsPage'
import Layout from './components/Layout'

function App() {
  const auth = useAuth()

  return (
    <BrowserRouter>
      {!auth.isAuthenticated ? (
        <LoginPage auth={auth} />
      ) : (
        <Layout onLogout={auth.logout}>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/review/:id" element={<EmailReviewPage />} />
            <Route path="/receipt/:id" element={<ReceiptTrackerPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<DashboardPage />} />
          </Routes>
        </Layout>
      )}
    </BrowserRouter>
  )
}

export default App
