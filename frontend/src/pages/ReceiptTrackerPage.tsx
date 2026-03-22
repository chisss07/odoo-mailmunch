import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import api from '../api/client'
import type { POTracking } from '../types'
import TrackingPanel from '../components/TrackingPanel'
import ReceiveForm from '../components/ReceiveForm'

interface POLine {
  product_name: string
  ordered_qty: number
  received_qty: number
}

interface PODetail extends POTracking {
  lines?: POLine[]
}

type AlertState = { type: 'success' | 'error'; message: string } | null

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-white/10 text-white/50',
  confirmed: 'bg-blue-500/20 text-blue-300',
  ordered: 'bg-blue-500/20 text-blue-300',
  shipped: 'bg-purple-500/20 text-purple-300',
  partial: 'bg-yellow-500/20 text-yellow-300',
  received: 'bg-green-500/20 text-green-300',
  done: 'bg-green-500/20 text-green-300',
  cancelled: 'bg-red-500/20 text-red-400',
}

export default function ReceiptTrackerPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [po, setPo] = useState<PODetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [alert, setAlert] = useState<AlertState>(null)

  const loadPO = async () => {
    if (!id) return
    setLoading(true)
    setLoadError('')
    try {
      const { data } = await api.get<PODetail>(`/pos/${id}`)
      setPo(data)
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setLoadError(err.response?.data?.detail ?? err.message)
      } else {
        setLoadError('Failed to load purchase order')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadPO()
  }, [id])

  const showAlert = (type: 'success' | 'error', message: string) => {
    setAlert({ type, message })
    setTimeout(() => setAlert(null), 4000)
  }

  const handleReceive = async (lines: { product_id: number; qty: number }[] | null) => {
    if (!id) return
    try {
      const body = lines ? { lines } : {}
      await api.post(`/pos/${id}/receive`, body)
      showAlert('success', lines ? 'Partial receipt recorded' : 'All items marked as received')
      await loadPO()
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail ?? err.message
        : 'Receipt failed'
      showAlert('error', message)
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

  if (!po) return null

  const statusClass = STATUS_COLORS[po.status] ?? 'bg-white/10 text-white/50'
  const lines: POLine[] = po.lines ?? []

  return (
    <div>
      {/* Page header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate('/')}
          className="text-white/40 hover:text-white/80 transition-colors"
          aria-label="Back"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-white text-xl font-semibold">Receipt Tracker</h1>
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

      {/* PO Header card */}
      <div className="bg-surface-light rounded-lg p-4 mb-4">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-white text-lg font-semibold">{po.odoo_po_name}</h2>
            <p className="text-white/50 text-sm mt-0.5">{po.vendor_name}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${statusClass}`}>
            {po.status}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm border-t border-white/10 pt-3">
          <div>
            <p className="text-white/40 text-xs mb-1">Purchase Order</p>
            <p className="text-white/80">{po.odoo_po_name}</p>
          </div>

          {po.sales_order_name && (
            <div>
              <p className="text-white/40 text-xs mb-1">Linked Sales Order</p>
              <p className="text-white/80">{po.sales_order_name}</p>
            </div>
          )}

          <div>
            <p className="text-white/40 text-xs mb-1">Created</p>
            <p className="text-white/60">
              {new Date(po.created_at).toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
              })}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Tracking */}
        <div>
          <TrackingPanel tracking={po.tracking_info} />
        </div>

        {/* Receipt form */}
        <div className="lg:col-span-2">
          <ReceiveForm
            poId={po.odoo_po_id}
            lines={lines}
            onReceive={handleReceive}
          />
        </div>
      </div>
    </div>
  )
}
