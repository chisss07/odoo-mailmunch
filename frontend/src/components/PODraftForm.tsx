import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import api from '../api/client'
import type { PODraft, LineItem } from '../types'
import ConfidenceBadge from './ConfidenceBadge'
import LineItemRow from './LineItemRow'

interface VendorResult {
  id: number
  name: string
  email: string
}

function VendorSelector({
  vendorName,
  vendorConfidence,
  onSelect,
}: {
  vendorName: string | null
  vendorConfidence: string
  onSelect: (id: number, name: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<VendorResult[]>([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    if (!open) {
      setQuery('')
      setResults([])
      setSearchError('')
      return
    }
    inputRef.current?.focus()
  }, [open])

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      return
    }
    const controller = new AbortController()
    const timer = setTimeout(async () => {
      setSearching(true)
      setSearchError('')
      try {
        const { data } = await api.get<VendorResult[]>('/odoo/vendors', {
          params: { q: query },
          signal: controller.signal,
        })
        setResults(data)
      } catch (err) {
        if (!axios.isAxiosError(err) || err.code !== 'ERR_CANCELED') {
          setSearchError('Search failed')
        }
      } finally {
        setSearching(false)
      }
    }, 300)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [query])

  const handleSelect = (vendor: VendorResult) => {
    onSelect(vendor.id, vendor.name)
    setOpen(false)
  }

  return (
    <div ref={containerRef} className="relative flex items-center gap-2">
      <span className="text-white text-sm font-medium">{vendorName || 'Unknown'}</span>
      <ConfidenceBadge confidence={vendorConfidence} />
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        title="Change vendor"
        className="p-0.5 rounded text-white/30 hover:text-white/70 hover:bg-white/10 transition-colors"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536M9 13l6.586-6.586a2 2 0 112.828 2.828L11.828 15.828a2 2 0 01-1.414.586H9v-2.414a2 2 0 01.586-1.414z" />
        </svg>
      </button>

      {open && (
        <div className="absolute z-50 top-full mt-1 left-0 w-80 bg-surface-light border border-white/10 rounded-lg shadow-xl">
          <div className="p-2 border-b border-white/10">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search vendors..."
              className="w-full bg-surface border border-white/20 text-white text-sm px-3 py-1.5 rounded focus:outline-none focus:border-primary placeholder-white/30"
            />
          </div>
          <div className="max-h-52 overflow-y-auto py-1">
            {searching && (
              <p className="text-white/40 text-xs px-3 py-2">Searching...</p>
            )}
            {searchError && (
              <p className="text-red-400 text-xs px-3 py-2">{searchError}</p>
            )}
            {!searching && results.length === 0 && query.trim() && (
              <p className="text-white/40 text-xs px-3 py-2">No vendors found</p>
            )}
            {!searching && !query.trim() && (
              <p className="text-white/30 text-xs px-3 py-2">Type to search vendors</p>
            )}
            {!searching &&
              results.map(vendor => (
                <button
                  key={vendor.id}
                  type="button"
                  onClick={() => handleSelect(vendor)}
                  className="w-full text-left px-3 py-2 hover:bg-white/10 flex flex-col gap-0.5"
                >
                  <span className="text-sm text-white/90 truncate">{vendor.name}</span>
                  {vendor.email && (
                    <span className="text-xs text-white/40 truncate">{vendor.email}</span>
                  )}
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

interface PODraftFormProps {
  draft: PODraft
  onSave: (draft: PODraft) => void
  onSubmit: (draftId: number) => void
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value)
}

export default function PODraftForm({ draft, onSave, onSubmit }: PODraftFormProps) {
  const handleLineUpdate = (index: number, updates: Partial<LineItem>) => {
    const updatedLines = draft.line_items.map((item, i) =>
      i === index ? { ...item, ...updates } : item
    )
    onSave({ ...draft, line_items: updatedLines })
  }

  const total = draft.line_items.reduce(
    (sum, item) => sum + item.quantity * item.unit_price,
    0
  )

  // Group items by SO for summary
  const soGroups = new Map<string, { name: string; total: number; count: number }>()
  for (const item of draft.line_items) {
    const key = item.sales_order_name || 'Stock (no SO)'
    const group = soGroups.get(key) || { name: key, total: 0, count: 0 }
    group.total += item.quantity * item.unit_price
    group.count += 1
    soGroups.set(key, group)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-surface-light rounded-t-lg px-4 py-3 border-b border-white/10">
        <h2 className="text-white/50 text-xs uppercase tracking-wider font-medium mb-3">
          PO Draft
        </h2>

        <VendorSelector
          vendorName={draft.vendor_name ?? null}
          vendorConfidence={draft.vendor_confidence}
          onSelect={(id, name) =>
            onSave({ ...draft, vendor_odoo_id: id, vendor_name: name, vendor_confidence: 'high' })
          }
        />

        {draft.expected_date && (
          <div className="mt-2">
            <p className="text-white/40 text-xs">Expected: {new Date(draft.expected_date).toLocaleDateString()}</p>
          </div>
        )}
      </div>

      {/* Line items */}
      <div className="flex-1 overflow-auto bg-surface-light">
        <div className="px-4 pt-3 pb-1">
          <div className="grid grid-cols-[2fr_1fr_1fr_60px_80px] gap-2 text-xs text-white/40 uppercase tracking-wider pb-2 border-b border-white/10">
            <span>Description</span>
            <span>Product</span>
            <span>Sales Order</span>
            <span className="text-right">Qty</span>
            <span className="text-right">Unit Price</span>
          </div>
        </div>

        <div className="px-4">
          {draft.line_items.length === 0 ? (
            <p className="text-white/30 text-sm py-6 text-center">No line items</p>
          ) : (
            draft.line_items.map((item, i) => (
              <LineItemRow
                key={i}
                item={item}
                index={i}
                onUpdate={handleLineUpdate}
              />
            ))
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="bg-surface-light rounded-b-lg px-4 py-3 border-t border-white/10">
        {/* SO breakdown */}
        {soGroups.size > 1 && (
          <div className="mb-3 space-y-1">
            {Array.from(soGroups.entries()).map(([key, group]) => (
              <div key={key} className="flex justify-between text-xs">
                <span className="text-white/40">
                  {group.name} ({group.count} {group.count === 1 ? 'item' : 'items'})
                </span>
                <span className="text-white/50">{formatCurrency(group.total)}</span>
              </div>
            ))}
            <div className="border-t border-white/10 pt-1" />
          </div>
        )}

        <div className="flex items-center justify-between mb-3">
          <span className="text-white/50 text-sm">Total</span>
          <span className="text-white font-semibold text-lg">{formatCurrency(total)}</span>
        </div>

        <div className="flex gap-2 justify-end">
          <button
            type="button"
            onClick={() => onSave(draft)}
            className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded text-sm border border-white/20 transition-colors"
          >
            Save Draft
          </button>
          <button
            type="button"
            onClick={() => onSubmit(draft.id)}
            className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded text-sm transition-colors"
          >
            Create PO in Odoo
          </button>
        </div>
      </div>
    </div>
  )
}
