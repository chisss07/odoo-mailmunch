import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import api from '../api/client'
import IgnoreRuleList from '../components/IgnoreRuleList'

// ─── Types ────────────────────────────────────────────────────────────────────

interface Setting {
  key: string
  value: string
  is_secret: boolean
}

interface OdooSession {
  odoo_url: string
  database: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const INPUT_CLASS =
  'w-full bg-surface border border-white/20 rounded px-3 py-2 text-white text-sm focus:border-primary focus:outline-none'

const M365_KEYS = [
  { key: 'm365_tenant_id', label: 'Tenant ID', secret: false },
  { key: 'm365_client_id', label: 'Client ID', secret: false },
  { key: 'm365_client_secret', label: 'Client Secret', secret: true },
  { key: 'm365_mailbox_folder', label: 'Mailbox Folder', secret: false },
] as const

// ─── Helpers ──────────────────────────────────────────────────────────────────

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-surface-light rounded-lg p-6 mb-4">
      <h2 className="text-white font-semibold text-base mb-4">{title}</h2>
      {children}
    </div>
  )
}

function StatusBadge({ ok, okLabel = 'Connected', failLabel = 'Not configured' }: {
  ok: boolean
  okLabel?: string
  failLabel?: string
}) {
  return ok ? (
    <span className="inline-flex items-center gap-1.5 text-xs text-green-400">
      <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
      {okLabel}
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 text-xs text-white/40">
      <span className="w-1.5 h-1.5 rounded-full bg-white/20 inline-block" />
      {failLabel}
    </span>
  )
}

// ─── M365 Setup Guide ────────────────────────────────────────────────────────

function M365SetupGuide() {
  const [open, setOpen] = useState(false)

  return (
    <div className="mb-4">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 text-sm text-primary hover:text-primary/80 transition-colors"
      >
        <svg
          className={`w-4 h-4 transition-transform ${open ? 'rotate-90' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        Setup Instructions
      </button>

      {open && (
        <div className="mt-3 bg-surface rounded-lg border border-white/10 p-4 text-sm text-white/70 space-y-4">
          <div>
            <h4 className="text-white font-medium mb-1">Step 1: Register an App in Azure</h4>
            <ol className="list-decimal list-inside space-y-1 text-white/60 text-xs leading-relaxed">
              <li>Go to <span className="text-primary">portal.azure.com</span> and sign in with your Microsoft 365 admin account</li>
              <li>Navigate to <span className="text-white/80">Azure Active Directory &gt; App registrations &gt; New registration</span></li>
              <li>Name it something like <span className="text-white/80">"MailMunch Email Reader"</span></li>
              <li>Set <span className="text-white/80">Supported account types</span> to "Accounts in this organizational directory only"</li>
              <li>Leave Redirect URI blank and click <span className="text-white/80">Register</span></li>
            </ol>
          </div>

          <div>
            <h4 className="text-white font-medium mb-1">Step 2: Copy the IDs</h4>
            <ol className="list-decimal list-inside space-y-1 text-white/60 text-xs leading-relaxed">
              <li>From the app's <span className="text-white/80">Overview</span> page, copy the <span className="text-white/80">Application (client) ID</span> &rarr; paste into <span className="text-primary">Client ID</span> below</li>
              <li>Copy the <span className="text-white/80">Directory (tenant) ID</span> &rarr; paste into <span className="text-primary">Tenant ID</span> below</li>
            </ol>
          </div>

          <div>
            <h4 className="text-white font-medium mb-1">Step 3: Create a Client Secret</h4>
            <ol className="list-decimal list-inside space-y-1 text-white/60 text-xs leading-relaxed">
              <li>Go to <span className="text-white/80">Certificates & secrets &gt; New client secret</span></li>
              <li>Add a description (e.g., "MailMunch") and pick an expiry (24 months recommended)</li>
              <li>Click <span className="text-white/80">Add</span>, then immediately copy the <span className="text-white/80">Value</span> column (not the Secret ID — the Value is only shown once)</li>
              <li>Paste it into <span className="text-primary">Client Secret</span> below</li>
            </ol>
          </div>

          <div>
            <h4 className="text-white font-medium mb-1">Step 4: Set API Permissions</h4>
            <ol className="list-decimal list-inside space-y-1 text-white/60 text-xs leading-relaxed">
              <li>Go to <span className="text-white/80">API permissions &gt; Add a permission &gt; Microsoft Graph</span></li>
              <li>Select <span className="text-white/80">Application permissions</span> (not Delegated)</li>
              <li>Search for and add: <span className="text-white/80">Mail.Read</span> (read-only — the app never modifies your mailbox)</li>
              <li>Click <span className="text-white/80">Grant admin consent for [your org]</span> and confirm</li>
              <li>Verify both permissions show a green checkmark under Status</li>
            </ol>
          </div>

          <div>
            <h4 className="text-white font-medium mb-1">Step 5: Configure Mailbox Folder</h4>
            <ul className="list-disc list-inside space-y-1 text-white/60 text-xs leading-relaxed">
              <li>Set <span className="text-primary">Mailbox Folder</span> to the folder name to monitor (default: <span className="text-white/80">Inbox</span>)</li>
              <li>Tip: Create a dedicated folder (e.g., "Vendor Orders") and set up an Outlook rule to route vendor emails there</li>
              <li>The poller checks every 5 minutes for unread messages and marks them as read after importing</li>
            </ul>
          </div>

          <div className="pt-2 border-t border-white/10">
            <p className="text-white/40 text-xs">
              Note: This uses app-only authentication (no user sign-in required). The app reads from the mailbox of the authenticated tenant. For shared/service mailboxes, additional Graph API scoping may be needed.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── M365 Section ─────────────────────────────────────────────────────────────

function M365Section({ settings }: { settings: Setting[] }) {
  const getVal = (key: string) => {
    const s = settings.find(s => s.key === key)
    return s?.value ?? ''
  }

  const [fields, setFields] = useState<Record<string, string>>({
    m365_tenant_id: '',
    m365_client_id: '',
    m365_client_secret: '',
    m365_mailbox_folder: '',
  })

  const [saving, setSaving] = useState<string | null>(null)
  const [savedKey, setSavedKey] = useState<string | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Sync incoming settings into local field state (skip masked secrets)
  useEffect(() => {
    setFields({
      m365_tenant_id: getVal('m365_tenant_id'),
      m365_client_id: getVal('m365_client_id'),
      // Leave secret blank so user must re-enter; show placeholder if masked
      m365_client_secret: '',
      m365_mailbox_folder: getVal('m365_mailbox_folder'),
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings])

  const isConfigured = !!getVal('m365_tenant_id') && !!getVal('m365_client_id')

  const handleSave = async (key: string, value: string) => {
    setSaving(key)
    setErrors(e => ({ ...e, [key]: '' }))
    try {
      await api.put('/settings', { key, value })
      setSavedKey(key)
      setTimeout(() => setSavedKey(k => (k === key ? null : k)), 2000)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setErrors(e => ({ ...e, [key]: err.response?.data?.detail || 'Save failed' }))
      } else {
        setErrors(e => ({ ...e, [key]: 'An unexpected error occurred' }))
      }
    } finally {
      setSaving(null)
    }
  }

  return (
    <SectionCard title="M365 Connection">
      <div className="flex items-center justify-between mb-4">
        <StatusBadge ok={isConfigured} />
      </div>

      <M365SetupGuide />

      <div className="space-y-4">
        {M365_KEYS.map(({ key, label, secret }) => (
          <div key={key}>
            <label className="block text-white/60 text-xs mb-1">{label}</label>
            <div className="flex gap-2">
              <input
                type={secret ? 'password' : 'text'}
                value={fields[key]}
                placeholder={
                  secret && getVal(key) === '****' ? 'Already set — enter new value to change' : ''
                }
                onChange={e => setFields(f => ({ ...f, [key]: e.target.value }))}
                className={INPUT_CLASS}
              />
              <button
                onClick={() => handleSave(key, fields[key])}
                disabled={saving === key}
                className="bg-primary hover:bg-primary/80 text-white text-sm px-4 py-2 rounded disabled:opacity-40 shrink-0"
              >
                {saving === key ? 'Saving...' : savedKey === key ? 'Saved' : 'Save'}
              </button>
            </div>
            {errors[key] && (
              <p className="text-red-400 text-xs mt-1">{errors[key]}</p>
            )}
          </div>
        ))}
      </div>
    </SectionCard>
  )
}

// ─── Odoo Section ─────────────────────────────────────────────────────────────

function OdooSection() {
  const [session, setSession] = useState<OdooSession | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await api.get<OdooSession>('/auth/session')
        setSession(data)
      } catch {
        // session endpoint may not exist; fail silently
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <SectionCard title="Odoo Connection">
      <div className="flex items-center justify-between mb-4">
        <StatusBadge ok={!!session} okLabel="Connected" failLabel="Unknown" />
      </div>

      {loading ? (
        <p className="text-white/40 text-sm">Loading...</p>
      ) : session ? (
        <div className="space-y-3">
          <div>
            <p className="text-white/50 text-xs mb-0.5">URL</p>
            <p className="text-white text-sm">{session.odoo_url}</p>
          </div>
          <div>
            <p className="text-white/50 text-xs mb-0.5">Database</p>
            <p className="text-white text-sm">{session.database}</p>
          </div>
        </div>
      ) : (
        <p className="text-white/40 text-sm">
          Connection details unavailable. You are authenticated via the login screen.
        </p>
      )}
    </SectionCard>
  )
}

// ─── Sync Settings Section ────────────────────────────────────────────────────

function SyncSection({ settings, onSettingsChange }: {
  settings: Setting[]
  onSettingsChange: () => void
}) {
  const getVal = (key: string) => settings.find(s => s.key === key)?.value ?? ''

  const autoSyncRaw = getVal('auto_sync_enabled')
  const autoSync = autoSyncRaw === 'true' || autoSyncRaw === '1'
  const lastProduct = getVal('last_product_cache_refresh')
  const lastVendor = getVal('last_vendor_cache_refresh')

  const [toggling, setToggling] = useState(false)
  const [toggleError, setToggleError] = useState('')
  const [refreshing, setRefreshing] = useState(false)
  const [refreshError, setRefreshError] = useState('')
  const [refreshDone, setRefreshDone] = useState(false)

  const handleToggle = async () => {
    setToggling(true)
    setToggleError('')
    try {
      await api.put('/settings', { key: 'auto_sync_enabled', value: String(!autoSync) })
      onSettingsChange()
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setToggleError(err.response?.data?.detail || 'Failed to update setting')
      } else {
        setToggleError('An unexpected error occurred')
      }
    } finally {
      setToggling(false)
    }
  }

  const handleRefreshCaches = async () => {
    setRefreshing(true)
    setRefreshError('')
    setRefreshDone(false)
    try {
      await api.post('/sync/refresh-caches')
      setRefreshDone(true)
      onSettingsChange()
      setTimeout(() => setRefreshDone(false), 3000)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setRefreshError(err.response?.data?.detail || 'Refresh failed')
      } else {
        setRefreshError('An unexpected error occurred')
      }
    } finally {
      setRefreshing(false)
    }
  }

  const formatDate = (val: string) => {
    if (!val) return 'Never'
    try {
      return new Date(val).toLocaleString()
    } catch {
      return val
    }
  }

  return (
    <SectionCard title="Sync Settings">
      <div className="space-y-4">
        {/* Auto-sync toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-white text-sm">Auto-sync</p>
            <p className="text-white/40 text-xs mt-0.5">Automatically process incoming emails</p>
          </div>
          <button
            role="switch"
            aria-checked={autoSync}
            onClick={handleToggle}
            disabled={toggling}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none disabled:opacity-40 ${
              autoSync ? 'bg-primary' : 'bg-white/20'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                autoSync ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {toggleError && (
          <p className="text-red-400 text-xs">{toggleError}</p>
        )}

        {/* Cache timestamps */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-white/10">
          <div>
            <p className="text-white/50 text-xs mb-0.5">Last Product Cache Refresh</p>
            <p className="text-white text-sm">{formatDate(lastProduct)}</p>
          </div>
          <div>
            <p className="text-white/50 text-xs mb-0.5">Last Vendor Cache Refresh</p>
            <p className="text-white text-sm">{formatDate(lastVendor)}</p>
          </div>
        </div>

        {/* Refresh button */}
        <div className="pt-2">
          <button
            onClick={handleRefreshCaches}
            disabled={refreshing}
            className="border border-white/20 text-white/70 hover:text-white text-sm px-4 py-2 rounded disabled:opacity-40"
          >
            {refreshing ? 'Refreshing...' : refreshDone ? 'Refreshed' : 'Refresh Caches Now'}
          </button>
          {refreshError && (
            <p className="text-red-400 text-xs mt-2">{refreshError}</p>
          )}
        </div>
      </div>
    </SectionCard>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [settings, setSettings] = useState<Setting[]>([])
  const [loadError, setLoadError] = useState('')

  const loadSettings = useCallback(async () => {
    setLoadError('')
    try {
      const { data } = await api.get<Setting[]>('/settings')
      setSettings(data)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setLoadError(err.response?.data?.detail || 'Failed to load settings')
      } else {
        setLoadError('An unexpected error occurred')
      }
    }
  }, [])

  useEffect(() => {
    loadSettings()
  }, [loadSettings])

  return (
    <div>
      <h1 className="text-white text-2xl font-semibold mb-6">Settings</h1>

      {loadError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-3 mb-4">
          <p className="text-red-400 text-sm">{loadError}</p>
        </div>
      )}

      <M365Section settings={settings} />

      <OdooSection />

      <SyncSection settings={settings} onSettingsChange={loadSettings} />

      <SectionCard title="Ignore Rules">
        <p className="text-white/50 text-xs mb-4">
          Emails matching these rules will be automatically skipped during processing.
        </p>
        <IgnoreRuleList />
      </SectionCard>
    </div>
  )
}
