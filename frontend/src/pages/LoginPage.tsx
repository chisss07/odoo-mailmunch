import { useState } from 'react'
import type { AuthMethod, LoginRequest } from '../types'

interface LoginPageProps {
  auth: {
    error: string
    login: (req: LoginRequest) => Promise<void>
  }
}

const COMMON_FIELDS: { key: keyof LoginRequest; label: string; type: string; placeholder?: string }[] = [
  { key: 'odoo_url', label: 'Odoo URL', type: 'text', placeholder: 'https://yourcompany.odoo.com' },
  { key: 'database', label: 'Database', type: 'text' },
  { key: 'email', label: 'Email', type: 'text' },
]

const CREDENTIAL_FIELD: Record<AuthMethod, { key: keyof LoginRequest; label: string; placeholder: string }> = {
  api_key: { key: 'api_key', label: 'API Key', placeholder: 'Odoo Settings → API Keys' },
  password: { key: 'password', label: 'Password', placeholder: 'Your Odoo password' },
}

export default function LoginPage({ auth }: LoginPageProps) {
  const [method, setMethod] = useState<AuthMethod>('api_key')
  const [form, setForm] = useState(() => ({
    odoo_url: localStorage.getItem('saved_odoo_url') || '',
    database: localStorage.getItem('saved_database') || '',
    email: localStorage.getItem('saved_email') || '',
    credential: '',
  }))

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    const { odoo_url, database, email, credential } = form
    auth.login({
      odoo_url,
      database,
      email,
      [method]: credential,
    })
  }

  const cred = CREDENTIAL_FIELD[method]

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center">
      <div className="bg-surface-light p-8 rounded-lg w-full max-w-sm">
        <h1 className="text-white text-xl font-semibold mb-6">MailMunch Login</h1>

        {/* Auth method toggle */}
        <div className="flex mb-5 bg-surface border border-white/20 rounded-lg p-1">
          {(['api_key', 'password'] as AuthMethod[]).map(m => (
            <button
              key={m}
              type="button"
              onClick={() => { setMethod(m); setForm(f => ({ ...f, credential: '' })) }}
              className={`flex-1 py-1.5 text-sm rounded-md transition-colors ${
                method === m
                  ? 'bg-primary text-white'
                  : 'text-white/50 hover:text-white/70'
              }`}
            >
              {m === 'api_key' ? 'API Key' : 'Password'}
            </button>
          ))}
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          {COMMON_FIELDS.map(({ key, label, type, placeholder }) => (
            <div key={key}>
              <label className="text-white/70 text-sm block mb-1">{label}</label>
              <input
                type={type}
                value={form[key as keyof typeof form] || ''}
                onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                placeholder={placeholder}
                className="w-full bg-surface border border-white/20 text-white px-3 py-2 rounded focus:outline-none focus:border-primary"
              />
            </div>
          ))}

          {/* Credential field (switches based on auth method) */}
          <div>
            <label className="text-white/70 text-sm block mb-1">{cred.label}</label>
            <input
              type="password"
              value={form.credential}
              onChange={e => setForm(f => ({ ...f, credential: e.target.value }))}
              placeholder={cred.placeholder}
              className="w-full bg-surface border border-white/20 text-white px-3 py-2 rounded focus:outline-none focus:border-primary"
            />
          </div>

          {method === 'password' && (
            <p className="text-white/40 text-xs">
              Note: Password login may not work if 2FA/TOTP is enabled. Use API Key instead.
            </p>
          )}

          {auth.error && <p className="text-red-400 text-sm">{auth.error}</p>}
          <button type="submit" className="w-full bg-primary hover:bg-primary-dark text-white py-2 rounded font-medium">
            Connect to Odoo
          </button>
        </form>
      </div>
    </div>
  )
}
