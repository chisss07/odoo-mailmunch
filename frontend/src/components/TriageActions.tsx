import { useState } from 'react'
import api from '../api/client'
import type { EmailRecord } from '../types'

interface TriageActionsProps {
  email: EmailRecord
  onAction?: () => void
}

export default function TriageActions({ email, onAction }: TriageActionsProps) {
  const [loading, setLoading] = useState(false)

  const act = async (action: string) => {
    setLoading(true)
    try {
      await api.post(`/triage/${email.id}/action`, { action })
      onAction?.()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex gap-2 flex-wrap">
      <button
        onClick={() => act('import_po')}
        disabled={loading}
        className="bg-primary hover:bg-primary-dark text-white px-3 py-1 rounded text-xs disabled:opacity-50"
      >
        Import as PO
      </button>
      <button
        onClick={() => act('track_shipment')}
        disabled={loading}
        className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-xs disabled:opacity-50"
      >
        Track Shipment
      </button>
      <button
        onClick={() => act('ignore')}
        disabled={loading}
        className="bg-white/10 hover:bg-white/20 text-white/70 px-3 py-1 rounded text-xs disabled:opacity-50"
      >
        Ignore
      </button>
      <button
        onClick={() => act('always_ignore_sender')}
        disabled={loading}
        className="bg-red-900/40 hover:bg-red-900/60 text-red-300 px-3 py-1 rounded text-xs disabled:opacity-50"
      >
        Always Ignore Sender
      </button>
    </div>
  )
}
