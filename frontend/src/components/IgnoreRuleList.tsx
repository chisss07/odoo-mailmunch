import { useEffect, useState, useCallback } from 'react'
import axios from 'axios'
import api from '../api/client'

interface IgnoreRule {
  id: number
  field: 'sender' | 'domain' | 'subject'
  match_type: 'exact' | 'contains' | 'regex'
  value: string
}

interface NewRuleForm {
  field: 'sender' | 'domain' | 'subject'
  match_type: 'exact' | 'contains' | 'regex'
  value: string
}

const FIELD_LABELS: Record<IgnoreRule['field'], string> = {
  sender: 'Sender',
  domain: 'Domain',
  subject: 'Subject',
}

const MATCH_TYPE_LABELS: Record<IgnoreRule['match_type'], string> = {
  exact: 'Exact',
  contains: 'Contains',
  regex: 'Regex',
}

const INPUT_CLASS =
  'w-full bg-surface border border-white/20 rounded px-3 py-2 text-white text-sm focus:border-primary focus:outline-none'

const SELECT_CLASS =
  'bg-surface border border-white/20 rounded px-3 py-2 text-white text-sm focus:border-primary focus:outline-none'

export default function IgnoreRuleList() {
  const [rules, setRules] = useState<IgnoreRule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleteError, setDeleteError] = useState('')
  const [addError, setAddError] = useState('')
  const [adding, setAdding] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const [form, setForm] = useState<NewRuleForm>({
    field: 'sender',
    match_type: 'contains',
    value: '',
  })

  const loadRules = useCallback(async () => {
    setError('')
    try {
      const { data } = await api.get<IgnoreRule[]>('/settings/ignore-rules')
      setRules(data)
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to load ignore rules')
      } else {
        setError('An unexpected error occurred')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadRules()
  }, [loadRules])

  const handleDelete = async (id: number) => {
    setDeleteError('')
    setDeletingId(id)
    try {
      await api.delete(`/settings/ignore-rules/${id}`)
      await loadRules()
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setDeleteError(err.response?.data?.detail || 'Failed to delete rule')
      } else {
        setDeleteError('An unexpected error occurred')
      }
    } finally {
      setDeletingId(null)
    }
  }

  const handleAdd = async () => {
    if (!form.value.trim()) {
      setAddError('Value is required')
      return
    }
    setAddError('')
    setAdding(true)
    try {
      await api.post('/settings/ignore-rules', form)
      setForm({ field: 'sender', match_type: 'contains', value: '' })
      await loadRules()
    } catch (err: unknown) {
      if (axios.isAxiosError(err)) {
        setAddError(err.response?.data?.detail || 'Failed to add rule')
      } else {
        setAddError('An unexpected error occurred')
      }
    } finally {
      setAdding(false)
    }
  }

  return (
    <div>
      {error && (
        <p className="text-red-400 text-sm mb-3">{error}</p>
      )}

      {loading ? (
        <p className="text-white/40 text-sm mb-4">Loading rules...</p>
      ) : rules.length === 0 ? (
        <p className="text-white/40 text-sm mb-4">No ignore rules configured.</p>
      ) : (
        <div className="mb-4 divide-y divide-white/5 border border-white/10 rounded-lg overflow-hidden">
          {rules.map(rule => (
            <div
              key={rule.id}
              className="flex items-center justify-between px-4 py-3 bg-surface"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded shrink-0">
                  {FIELD_LABELS[rule.field]}
                </span>
                <span className="text-xs text-white/50 bg-white/5 px-2 py-0.5 rounded shrink-0">
                  {MATCH_TYPE_LABELS[rule.match_type]}
                </span>
                <span className="text-sm text-white truncate" title={rule.value}>
                  {rule.value}
                </span>
              </div>
              <button
                onClick={() => handleDelete(rule.id)}
                disabled={deletingId === rule.id}
                className="ml-4 text-xs text-red-400 hover:text-red-300 disabled:opacity-40 shrink-0"
              >
                {deletingId === rule.id ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          ))}
        </div>
      )}

      {deleteError && (
        <p className="text-red-400 text-sm mb-3">{deleteError}</p>
      )}

      <div className="border border-white/10 rounded-lg p-4 bg-surface">
        <p className="text-white/70 text-xs font-medium uppercase tracking-wide mb-3">Add Rule</p>
        <div className="flex flex-col sm:flex-row gap-3 items-start">
          <select
            value={form.field}
            onChange={e => setForm(f => ({ ...f, field: e.target.value as IgnoreRule['field'] }))}
            className={SELECT_CLASS}
          >
            <option value="sender">Sender</option>
            <option value="domain">Domain</option>
            <option value="subject">Subject</option>
          </select>

          <select
            value={form.match_type}
            onChange={e =>
              setForm(f => ({ ...f, match_type: e.target.value as IgnoreRule['match_type'] }))
            }
            className={SELECT_CLASS}
          >
            <option value="exact">Exact</option>
            <option value="contains">Contains</option>
            <option value="regex">Regex</option>
          </select>

          <input
            type="text"
            placeholder="Value"
            value={form.value}
            onChange={e => setForm(f => ({ ...f, value: e.target.value }))}
            onKeyDown={e => { if (e.key === 'Enter') handleAdd() }}
            className={INPUT_CLASS}
          />

          <button
            onClick={handleAdd}
            disabled={adding}
            className="bg-primary hover:bg-primary/80 text-white text-sm px-4 py-2 rounded disabled:opacity-40 shrink-0"
          >
            {adding ? 'Adding...' : 'Add'}
          </button>
        </div>

        {addError && (
          <p className="text-red-400 text-sm mt-2">{addError}</p>
        )}
      </div>
    </div>
  )
}
