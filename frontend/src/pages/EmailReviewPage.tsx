import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import api from '../api/client'
import type { PODraft } from '../types'
import EmailViewer from '../components/EmailViewer'
import PODraftForm from '../components/PODraftForm'

interface EmailDetail {
  id: number
  sender: string
  subject: string
  body_text: string
  body_html?: string
  attachment_paths?: string[]
  status: string
}

type AlertState = { type: 'success' | 'error'; message: string } | null

export default function EmailReviewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [email, setEmail] = useState<EmailDetail | null>(null)
  const [draft, setDraft] = useState<PODraft | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [saving, setSaving] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [reprocessing, setReprocessing] = useState(false)
  const [alert, setAlert] = useState<AlertState>(null)
  const [emailCollapsed, setEmailCollapsed] = useState(false)

  useEffect(() => {
    if (!id) return
    const load = async () => {
      setLoading(true)
      setLoadError('')
      try {
        const [emailRes, draftsRes] = await Promise.all([
          api.get<EmailDetail>(`/emails/${id}`),
          api.get<PODraft[]>('/drafts', { params: { email_id: id } }),
        ])
        setEmail(emailRes.data)
        setDraft(draftsRes.data[0] ?? null)
      } catch (err) {
        if (axios.isAxiosError(err)) {
          setLoadError(err.response?.data?.detail ?? err.message)
        } else {
          setLoadError('Failed to load email')
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const showAlert = (type: 'success' | 'error', message: string) => {
    setAlert({ type, message })
    setTimeout(() => setAlert(null), 4000)
  }

  const handleSave = async (updatedDraft: PODraft) => {
    if (!draft) return
    setSaving(true)
    try {
      const { data } = await api.put<PODraft>(`/drafts/${draft.id}`, updatedDraft)
      setDraft(data)
      showAlert('success', 'Draft saved')
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail ?? err.message
        : 'Save failed'
      showAlert('error', message)
    } finally {
      setSaving(false)
    }
  }

  const handleSubmit = async (draftId: number) => {
    setSubmitting(true)
    try {
      await api.post(`/drafts/${draftId}/submit`)
      showAlert('success', 'PO created in Odoo')
      setTimeout(() => navigate('/'), 1500)
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail ?? err.message
        : 'Submit failed'
      showAlert('error', message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-white/40 text-sm">Loading...</p>
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
        <p className="text-red-400 text-sm">{loadError}</p>
        <button
          onClick={() => navigate('/')}
          className="mt-3 text-white/60 hover:text-white text-sm underline"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  if (!email) return null

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="text-white/40 hover:text-white/80 transition-colors"
            aria-label="Back"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <h1 className="text-white text-xl font-semibold">Email Review</h1>
        </div>

        {(saving || submitting) && (
          <p className="text-white/50 text-sm">{saving ? 'Saving...' : 'Submitting...'}</p>
        )}
      </div>

      {/* Alert banner */}
      {alert && (
        <div
          className={`mb-4 px-4 py-2.5 rounded-lg text-sm ${
            alert.type === 'success'
              ? 'bg-green-500/15 border border-green-500/30 text-green-300'
              : 'bg-red-500/15 border border-red-500/30 text-red-400'
          }`}
        >
          {alert.message}
        </div>
      )}

      {/* Split view */}
      <div
        className={`grid gap-4 flex-1 min-h-0 transition-all duration-300 ${
          emailCollapsed ? 'grid-cols-[auto_1fr]' : 'grid-cols-[2fr_3fr]'
        }`}
        style={{ height: 'calc(100vh - 180px)' }}
      >
        {/* Left: Email viewer */}
        <div className={`overflow-hidden flex flex-col min-w-0 ${emailCollapsed ? 'w-8' : ''}`}>
          {emailCollapsed ? (
            <div className="flex flex-col items-center h-full bg-surface-light rounded-lg border border-white/10">
              <button
                type="button"
                onClick={() => setEmailCollapsed(false)}
                title="Expand email panel"
                className="flex flex-col items-center gap-2 pt-3 px-2 text-white/40 hover:text-white/80 transition-colors w-full"
              >
                <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                <span
                  className="text-xs font-medium tracking-wider whitespace-nowrap"
                  style={{ writingMode: 'vertical-rl', textOrientation: 'mixed', transform: 'rotate(180deg)' }}
                >
                  Email
                </span>
              </button>
            </div>
          ) : (
            <div className="relative flex flex-col h-full">
              <button
                type="button"
                onClick={() => setEmailCollapsed(true)}
                title="Collapse email panel"
                className="absolute top-2 right-2 z-10 p-1 rounded text-white/30 hover:text-white/70 hover:bg-white/10 transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <EmailViewer email={email} />
            </div>
          )}
        </div>

        {/* Right: PO draft form */}
        <div className="overflow-hidden flex flex-col min-w-0">
          {draft ? (
            <PODraftForm
              draft={draft}
              onSave={handleSave}
              onSubmit={handleSubmit}
            />
          ) : (
            <div className="bg-surface-light rounded-lg flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-white/40 text-sm">No draft found for this email</p>
                <p className="text-white/25 text-xs mt-1">
                  The email may still be processing or was not recognized as a PO
                </p>
                <button
                  onClick={async () => {
                    setReprocessing(true)
                    try {
                      await api.post(`/emails/${id}/reprocess`)
                      showAlert('success', 'Email queued for reprocessing')
                      // Reload after a short delay to pick up the new draft
                      setTimeout(() => window.location.reload(), 3000)
                    } catch (err) {
                      const message = axios.isAxiosError(err)
                        ? err.response?.data?.detail ?? err.message
                        : 'Reprocess failed'
                      showAlert('error', message)
                    } finally {
                      setReprocessing(false)
                    }
                  }}
                  disabled={reprocessing}
                  className="mt-4 bg-primary hover:bg-primary/80 text-white text-sm px-4 py-2 rounded disabled:opacity-40"
                >
                  {reprocessing ? 'Reprocessing...' : 'Reprocess Email'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
