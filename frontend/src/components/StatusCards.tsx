import { useEffect, useState } from 'react'
import api from '../api/client'

interface Counts {
  triage: number
  processing: number
  ordered: number
  shipped: number
  partial: number
  received: number
}

export default function StatusCards() {
  const [counts, setCounts] = useState<Counts>({
    triage: 0,
    processing: 0,
    ordered: 0,
    shipped: 0,
    partial: 0,
    received: 0,
  })

  useEffect(() => {
    const load = async () => {
      try {
        const [emailsRes, posRes] = await Promise.all([
          api.get<{ status: string }[]>('/emails'),
          api.get<{ status: string }[]>('/pos'),
        ])
        const emails = emailsRes.data
        const pos = posRes.data
        setCounts({
          triage: emails.filter(e => e.status === 'triage').length,
          processing: emails.filter(e => e.status === 'processing').length,
          ordered: pos.filter(p => p.status === 'ordered' || p.status === 'confirmed').length,
          shipped: pos.filter(p => p.status === 'shipped').length,
          partial: pos.filter(p => p.status === 'partial').length,
          received: pos.filter(p => p.status === 'received').length,
        })
      } catch {
        // ignore errors silently
      }
    }
    load()
  }, [])

  const cards = [
    { label: 'Triage', count: counts.triage, icon: '📥', color: 'text-yellow-400' },
    { label: 'Processing', count: counts.processing, icon: '⚙️', color: 'text-blue-400' },
    { label: 'Ordered', count: counts.ordered, icon: '🛒', color: 'text-primary' },
    { label: 'Shipped', count: counts.shipped, icon: '🚚', color: 'text-purple-400' },
    { label: 'Partial', count: counts.partial, icon: '📦', color: 'text-orange-400' },
    { label: 'Completed', count: counts.received, icon: '✅', color: 'text-green-400' },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
      {cards.map(card => (
        <div key={card.label} className="bg-surface-light rounded-lg p-4 flex flex-col items-center">
          <span className="text-2xl mb-1">{card.icon}</span>
          <span className={`text-2xl font-bold ${card.color}`}>{card.count}</span>
          <span className="text-white/60 text-xs mt-1">{card.label}</span>
        </div>
      ))}
    </div>
  )
}
