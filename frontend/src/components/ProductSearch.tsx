import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import api from '../api/client'
import ConfidenceBadge from './ConfidenceBadge'

interface Alternative {
  odoo_id: number
  name: string
  score: number
}

interface ProductSearchProps {
  currentMatch: {
    odoo_id: number | null
    name: string | null
    confidence: string
  }
  alternatives: Alternative[]
  onSelect: (odooId: number, name: string) => void
}

interface SearchResult {
  odoo_id: number
  name: string
}

export default function ProductSearch({ currentMatch, alternatives, onSelect }: ProductSearchProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
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
        const { data } = await api.get<SearchResult[]>('/odoo/products', {
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

  const handleSelect = (odooId: number, name: string) => {
    onSelect(odooId, name)
    setOpen(false)
  }

  const displayName = currentMatch.name ?? 'No match'

  const listItems: { odoo_id: number; name: string; score?: number }[] =
    query.trim() ? results : alternatives

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="flex items-center gap-2 text-left w-full group"
      >
        <span className="text-white/90 text-sm truncate max-w-[180px]">{displayName}</span>
        <ConfidenceBadge confidence={currentMatch.confidence} />
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
        <div className="absolute z-50 top-full mt-1 left-0 w-72 bg-surface-light border border-white/10 rounded-lg shadow-xl">
          <div className="p-2 border-b border-white/10">
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search products..."
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
            {!searching && listItems.length === 0 && query.trim() && (
              <p className="text-white/40 text-xs px-3 py-2">No products found</p>
            )}
            {!searching &&
              listItems.map(item => (
                <button
                  key={item.odoo_id}
                  type="button"
                  onClick={() => handleSelect(item.odoo_id, item.name)}
                  className="w-full text-left px-3 py-2 text-sm text-white/80 hover:bg-white/10 flex items-center justify-between gap-2"
                >
                  <span className="truncate">{item.name}</span>
                  {'score' in item && item.score !== undefined && (
                    <span className="text-white/30 text-xs flex-shrink-0">
                      {Math.round(item.score * 100)}%
                    </span>
                  )}
                </button>
              ))}
            <button
              type="button"
              onClick={() => handleSelect(0, 'No match')}
              className="w-full text-left px-3 py-2 text-sm text-white/40 hover:bg-white/10 border-t border-white/5 mt-1"
            >
              No match
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
