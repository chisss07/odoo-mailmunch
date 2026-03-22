import { useState } from 'react'
import type { LoginRequest } from '../types'

interface AuthHook {
  needsTotp: boolean
  error: string
  login: (req: LoginRequest) => Promise<void>
  submitTotp: (code: string) => Promise<void>
}

interface LoginPageProps {
  auth: AuthHook
}

export default function LoginPage({ auth }: LoginPageProps) {
  const [form, setForm] = useState({ odoo_url: '', database: '', email: '', password: '' })
  const [totpCode, setTotpCode] = useState('')

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    auth.login(form)
  }

  const handleTotp = (e: React.FormEvent) => {
    e.preventDefault()
    auth.submitTotp(totpCode)
  }

  if (auth.needsTotp) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <div className="bg-surface-light p-8 rounded-lg w-full max-w-sm">
          <h1 className="text-white text-xl font-semibold mb-6">Two-Factor Authentication</h1>
          <form onSubmit={handleTotp} className="space-y-4">
            <div>
              <label className="text-white/70 text-sm block mb-1">Authenticator Code</label>
              <input
                type="text"
                value={totpCode}
                onChange={e => setTotpCode(e.target.value)}
                placeholder="000000"
                className="w-full bg-surface border border-white/20 text-white px-3 py-2 rounded focus:outline-none focus:border-primary"
              />
            </div>
            {auth.error && <p className="text-red-400 text-sm">{auth.error}</p>}
            <button type="submit" className="w-full bg-primary hover:bg-primary-dark text-white py-2 rounded font-medium">
              Verify
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="bg-surface-light p-8 rounded-lg w-full max-w-sm">
        <h1 className="text-white text-xl font-semibold mb-6">MailMunch Login</h1>
        <form onSubmit={handleLogin} className="space-y-4">
          {(['odoo_url', 'database', 'email', 'password'] as const).map((field) => (
            <div key={field}>
              <label className="text-white/70 text-sm block mb-1 capitalize">{field.replace('_', ' ')}</label>
              <input
                type={field === 'password' ? 'password' : 'text'}
                value={form[field]}
                onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))}
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
