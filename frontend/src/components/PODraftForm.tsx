import type { PODraft, LineItem } from '../types'
import ConfidenceBadge from './ConfidenceBadge'
import LineItemRow from './LineItemRow'

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

        <div className="flex items-center gap-2">
          <span className="text-white text-sm font-medium">{draft.vendor_name || 'Unknown'}</span>
          <ConfidenceBadge confidence={draft.vendor_confidence} />
        </div>

        {draft.expected_date && (
          <div className="mt-2">
            <p className="text-white/40 text-xs">Expected: {new Date(draft.expected_date).toLocaleDateString()}</p>
          </div>
        )}
      </div>

      {/* Line items */}
      <div className="flex-1 overflow-auto bg-surface-light">
        <div className="px-4 pt-3 pb-1">
          <div className="grid grid-cols-[1fr_160px_160px_60px_80px_80px_60px] gap-2 text-xs text-white/40 uppercase tracking-wider pb-2 border-b border-white/10">
            <span>Description</span>
            <span>Product</span>
            <span>Sales Order</span>
            <span className="text-right">Qty</span>
            <span className="text-right">Unit Price</span>
            <span className="text-right">Subtotal</span>
            <span className="text-right">Conf.</span>
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
