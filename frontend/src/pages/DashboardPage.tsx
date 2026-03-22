import { useEffect, useState } from 'react'
import api from '../api/client'
import type { EmailRecord } from '../types'
import StatusCards from '../components/StatusCards'
import FileUpload from '../components/FileUpload'
import POTable from '../components/POTable'
import TriageActions from '../components/TriageActions'

export default function DashboardPage() {
  const [emails, setEmails] = useState<EmailRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  const loadEmails = async () => {
    try {
      const { data } = await api.get<EmailRecord[]>('/emails')
      setEmails(data)
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadEmails()
  }, [refreshKey])

  const triageEmails = emails.filter(e => e.status === 'triage')

  return (
    <div>
      <h1 className="text-white text-2xl font-semibold mb-6">Dashboard</h1>

      <StatusCards />

      <FileUpload onUploaded={() => setRefreshKey(k => k + 1)} />

      {triageEmails.length > 0 && (
        <div className="mb-6">
          <h2 className="text-white/80 text-sm font-medium mb-3">Needs Triage</h2>
          <div className="bg-surface-light rounded-lg divide-y divide-white/5">
            {triageEmails.map(email => (
              <div key={email.id} className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="text-white text-sm font-medium">{email.subject}</p>
                    <p className="text-white/50 text-xs">{email.sender}</p>
                  </div>
                  <span className="text-white/30 text-xs">
                    {new Date(email.created_at).toLocaleDateString()}
                  </span>
                </div>
                <TriageActions email={email} onAction={() => setRefreshKey(k => k + 1)} />
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h2 className="text-white/80 text-sm font-medium mb-3">All Emails</h2>
        <div className="bg-surface-light rounded-lg p-4">
          {loading ? (
            <p className="text-white/40 text-sm">Loading...</p>
          ) : (
            <POTable emails={emails} />
          )}
        </div>
      </div>
    </div>
  )
}
