import { useState } from 'react'

interface POLine {
  product_name: string
  ordered_qty: number
  received_qty: number
}

interface ReceiveFormProps {
  poId: number
  lines: POLine[]
  onReceive: (lines: { product_id: number; qty: number }[] | null) => void
}

export default function ReceiveForm({ poId: _poId, lines, onReceive }: ReceiveFormProps) {
  const [receiving, setReceiving] = useState<Record<number, string>>(
    () =>
      Object.fromEntries(
        lines.map((line, i) => {
          const remaining = Math.max(0, line.ordered_qty - line.received_qty)
          return [i, String(remaining)]
        })
      )
  )
  const [submitting, setSubmitting] = useState(false)

  const handleQtyChange = (index: number, value: string) => {
    setReceiving(prev => ({ ...prev, [index]: value }))
  }

  const handleReceiveAll = async () => {
    setSubmitting(true)
    try {
      await onReceive(null)
    } finally {
      setSubmitting(false)
    }
  }

  const handlePartialReceive = async () => {
    const partialLines = Object.entries(receiving)
      .map(([i, qty]) => ({
        product_id: parseInt(i, 10),
        qty: parseFloat(qty) || 0,
      }))
      .filter(l => l.qty > 0)

    if (partialLines.length === 0) return

    setSubmitting(true)
    try {
      await onReceive(partialLines)
    } finally {
      setSubmitting(false)
    }
  }

  const allReceived = lines.every(l => l.received_qty >= l.ordered_qty)

  if (allReceived) {
    return (
      <div className="bg-surface-light rounded-lg p-4">
        <h3 className="text-white/50 text-xs uppercase tracking-wider font-medium mb-3">
          Receipt
        </h3>
        <div className="flex items-center gap-2 text-green-400">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-sm">All items received</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-surface-light rounded-lg p-4">
      <h3 className="text-white/50 text-xs uppercase tracking-wider font-medium mb-3">
        Receive Items
      </h3>

      <div className="overflow-x-auto">
        <table className="w-full text-sm mb-4">
          <thead>
            <tr className="text-white/40 text-left border-b border-white/10">
              <th className="pb-2 font-medium pr-4">Product</th>
              <th className="pb-2 font-medium pr-4 text-right">Ordered</th>
              <th className="pb-2 font-medium pr-4 text-right">Received</th>
              <th className="pb-2 font-medium text-right">Receiving Now</th>
            </tr>
          </thead>
          <tbody>
            {lines.map((line, i) => {
              const remaining = Math.max(0, line.ordered_qty - line.received_qty)
              const isFullyReceived = line.received_qty >= line.ordered_qty
              return (
                <tr key={i} className="border-b border-white/5">
                  <td className="py-2 pr-4 text-white/80">{line.product_name}</td>
                  <td className="py-2 pr-4 text-right text-white/60">
                    {line.ordered_qty}
                  </td>
                  <td className="py-2 pr-4 text-right">
                    <span
                      className={
                        isFullyReceived
                          ? 'text-green-400'
                          : line.received_qty > 0
                          ? 'text-yellow-400'
                          : 'text-white/40'
                      }
                    >
                      {line.received_qty}
                    </span>
                  </td>
                  <td className="py-2 text-right">
                    {isFullyReceived ? (
                      <span className="text-green-400 text-xs">Done</span>
                    ) : (
                      <input
                        type="number"
                        min={0}
                        max={remaining}
                        step="any"
                        value={receiving[i] ?? ''}
                        onChange={e => handleQtyChange(i, e.target.value)}
                        className="w-20 bg-surface border border-white/20 text-white text-sm px-2 py-1 rounded focus:outline-none focus:border-primary text-right"
                        placeholder={String(remaining)}
                      />
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={handlePartialReceive}
          disabled={submitting}
          className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded text-sm border border-white/20 transition-colors disabled:opacity-50"
        >
          Partial Receive
        </button>
        <button
          type="button"
          onClick={handleReceiveAll}
          disabled={submitting}
          className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded text-sm transition-colors disabled:opacity-50"
        >
          {submitting ? 'Receiving...' : 'Receive All'}
        </button>
      </div>
    </div>
  )
}
