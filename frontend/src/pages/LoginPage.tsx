import { useState } from 'react'
import type { LoginRequest } from '../types'

interface LoginPageProps {
  auth: {
    error: string
    login: (req: LoginRequest) => Promise<void>
  }
}

const FIELDS: { key: keyof LoginRequest; label: string; type: string; placeholder?: string }[] = [
  { key: 'odoo_url', label: 'Odoo URL', type: 'text', placeholder: 'https://yourcompany.odoo.com' },
  { key: 'database', label: 'Database', type: 'text' },
  { key: 'email', label: 'Email', type: 'text' },
  { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'Odoo Settings → API Keys' },
]

export default function LoginPage({ auth }: LoginPageProps) {
  const [form, setForm] = useState<LoginRequest>({ odoo_url: '', database: '', email: '', api_key: '' })

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    auth.login(form)
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="bg-surface-light p-8 rounded-lg w-full max-w-sm">
        <h1 className="text-white text-xl font-semibold mb-6">MailMunch Login</h1>
        <form onSubmit={handleLogin} className="space-y-4">
          {FIELDS.map(({ key, label, type, placeholder }) => (
            <div key={key}>
              <label className="text-white/70 text-sm block mb-1">{label}</label>
              <input
                type={type}
                value={form[key]}
                onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                placeholder={placeholder}
                className="w-full bg-surface border border-white/20 text-white px-3 py-2 rounded focus:outline-none focus:border-primary"
              />
            </div>
          ))}
          {auth.error && <p className="text-red-400 text-sm">{auth.error}</p>}
          <button type="submit" className="w-full bg-primary hover:bg-primary-dark text-white py-2 rounded font-medium">
            Connect to Odoo
          </button>
        </form>
      </div>
    </div>
  )
}
