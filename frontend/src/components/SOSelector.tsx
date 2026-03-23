import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import api from '../api/client'
import type { SalesOrder } from '../types'

interface SOSelectorProps {
  value: { id: number | null; name: string | null }
  onSelect: (id: number, name: string) => void
  compact?: boolean
}

export default function SOSelector({ value, onSelect, compact }: SOSelectorProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SalesOrder[]>([])
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
    const controller = new AbortController()
    const timer = setTimeout(async () => {
      setSearching(true)
      setSearchError('')
      try {
        const { data } = await api.get<SalesOrder[]>('/odoo/sales-orders', {
          params: { q: query.trim() || undefined },
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
  }, [query, open])

  const handleSelect = (so: SalesOrder) => {
    onSelect(so.id, so.name)
    setOpen(false)
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onSelect(0, '')
  }

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className={`flex items-center gap-1 text-left w-full bg-surface border border-white/20 rounded hover:border-white/40 transition-colors ${compact ? 'px-2 py-1' : 'px-3 py-1.5'}`}
      >
        <span className={`flex-1 truncate ${compact ? 'text-xs' : 'text-sm'}`}>
          {value.name ? (
            <span className="text-white">{value.name}</span>
          ) : (
            <span className="text-white/30">{compact ? 'SO...' : 'Link Sales Order...'}</span>
          )}
        </span>
        {value.name && (
          <span
            role="button"
            tabIndex={0}
            onClick={handleClear}
            onKeyDown={e => e.key === 'Enter' && handleClear(e as unknown as React.MouseEvent)}
            className="text-white/30 hover:text-white/60 text-xs px-1"
          >
            x
          </span>
        )}
        <svg
          className={`w-3.5 h-3.5 text-white/30 flex-shrink-0 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div className="absolute z-50 top-full mt-1 left-0 w-full min-w-[280px] bg-surface-light border border-white/10 rounded-lg shadow-xl">
          <div className="p-2 border-b border-white/10">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search sales orders..."
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
            {!searching && results.length === 0 && (
              <p className="text-white/40 text-xs px-3 py-2">
                {query.trim() ? 'No sales orders found' : 'Type to search'}
              </p>
            )}
            {!searching &&
              results.map(so => (
                <button
                  key={so.id}
                  type="button"
                  onClick={() => handleSelect(so)}
                  className="w-full text-left px-3 py-2 hover:bg-white/10 group"
                >
                  <div className="text-sm text-white group-hover:text-white">{so.name}</div>
                  <div className="text-xs text-white/40">
                    {Array.isArray(so.partner_id) ? so.partner_id[1] : so.partner_id}
                  </div>
                </button>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
