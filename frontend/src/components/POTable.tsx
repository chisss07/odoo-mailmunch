import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import type { EmailRecord } from '../types'

interface POTableProps {
  emails: EmailRecord[]
  onRefresh?: () => void
}

const STATUS_COLORS: Record<string, string> = {
  triage: 'bg-yellow-500/20 text-yellow-300',
  processing: 'bg-blue-500/20 text-blue-300',
  reviewed: 'bg-green-500/20 text-green-300',
  ignored: 'bg-white/10 text-white/40',
}

export default function POTable({ emails, onRefresh }: POTableProps) {
  const navigate = useNavigate()

  if (emails.length === 0) {
    return (
      <p className="text-white/40 text-sm py-4">
        No emails yet. Upload or paste an email to get started.
      </p>
    )
  }

  const handleCancel = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation()
    await api.post(`/emails/${id}/cancel`)
    onRefresh?.()
  }

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation()
    if (!confirm('Delete this email?')) return
    await api.delete(`/emails/${id}`)
    onRefresh?.()
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-white/40 text-left border-b border-white/10">
            <th className="pb-2 pr-4 font-medium">Sender</th>
            <th className="pb-2 pr-4 font-medium">Subject</th>
            <th className="pb-2 pr-4 font-medium">Status</th>
            <th className="pb-2 pr-4 font-medium">Classification</th>
            <th className="pb-2 pr-4 font-medium">Date</th>
            <th className="pb-2 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {emails.map(email => (
            <tr
              key={email.id}
              onClick={() => navigate(`/review/${email.id}`)}
              className="border-b border-white/5 hover:bg-white/5 cursor-pointer"
            >
              <td className="py-2 pr-4 text-white/80 truncate max-w-[200px]">{email.sender}</td>
              <td className="py-2 pr-4 text-white truncate max-w-[300px]">{email.subject}</td>
              <td className="py-2 pr-4">
                <span
                  className={`px-2 py-0.5 rounded text-xs ${
                    STATUS_COLORS[email.status] ?? 'bg-white/10 text-white/50'
                  }`}
                >
                  {email.status}
                </span>
              </td>
              <td className="py-2 pr-4 text-white/60 capitalize">
                {email.classification.replace('_', ' ')}
              </td>
              <td className="py-2 pr-4 text-white/40">
                {new Date(email.created_at).toLocaleDateString()}
              </td>
              <td className="py-2">
                <div className="flex gap-1">
                  {email.status === 'processing' && (
                    <button
                      onClick={e => handleCancel(e, email.id)}
                      className="px-2 py-0.5 text-xs rounded bg-yellow-500/20 text-yellow-300 hover:bg-yellow-500/30"
                    >
                      Cancel
                    </button>
                  )}
                  <button
                    onClick={e => handleDelete(e, email.id)}
                    className="px-2 py-0.5 text-xs rounded bg-red-500/20 text-red-300 hover:bg-red-500/30"
                  >
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
