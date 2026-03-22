import { Link } from 'react-router-dom'

interface LayoutProps {
  children: React.ReactNode
  onLogout: () => void
}

export default function Layout({ children, onLogout }: LayoutProps) {
  return (
    <div className="min-h-screen bg-surface text-white">
      <nav className="bg-surface-light border-b border-white/10 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <span className="text-primary font-bold text-lg">MailMunch</span>
          <Link to="/" className="text-sm text-white/70 hover:text-white">Dashboard</Link>
          <Link to="/settings" className="text-sm text-white/70 hover:text-white">Settings</Link>
        </div>
        <button
          onClick={onLogout}
          className="text-sm text-white/70 hover:text-white px-3 py-1 border border-white/20 rounded"
        >
          Logout
        </button>
      </nav>
      <main className="p-6">{children}</main>
    </div>
  )
}
