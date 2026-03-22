import type { PODraft, LineItem } from '../types'
import ConfidenceBadge from './ConfidenceBadge'
import SOSelector from './SOSelector'
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

  const handleSOSelect = (id: number, name: string) => {
    onSave({
      ...draft,
      sales_order_id: id || null,
      sales_order_name: name || null,
    })
  }

  const total = draft.line_items.reduce(
    (sum, item) => sum + item.quantity * item.unit_price,
    0
  )

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="bg-surface-light rounded-t-lg px-4 py-3 border-b border-white/10">
        <h2 className="text-white/50 text-xs uppercase tracking-wider font-medium mb-3">
          PO Draft
        </h2>

        <div className="grid grid-cols-2 gap-4">
          {/* Vendor */}
          <div>
            <p className="text-white/40 text-xs mb-1">Vendor</p>
            <div className="flex items-center gap-2">
              <span className="text-white text-sm font-medium">{draft.vendor_name || 'Unknown'}</span>
              <ConfidenceBadge confidence={draft.vendor_confidence} />
            </div>
          </div>

          {/* Sales Order */}
          <div>
            <p className="text-white/40 text-xs mb-1">Sales Order</p>
            <SOSelector
              value={{ id: draft.sales_order_id, name: draft.sales_order_name }}
              onSelect={handleSOSelect}
            />
          </div>
        </div>

        {draft.expected_date && (
          <div className="mt-3">
            <p className="text-white/40 text-xs mb-1">Expected Date</p>
            <p className="text-white/80 text-sm">
              {new Date(draft.expected_date).toLocaleDateString()}
            </p>
          </div>
        )}
      </div>

      {/* Line items */}
      <div className="flex-1 overflow-auto bg-surface-light">
        <div className="px-4 pt-3 pb-1">
          <div className="grid grid-cols-[1fr_200px_80px_90px_90px_80px] gap-3 text-xs text-white/40 uppercase tracking-wider pb-2 border-b border-white/10">
            <span>Description</span>
            <span>Product</span>
            <span className="text-right">Qty</span>
            <span className="text-right">Unit Price</span>
            <span className="text-right">Subtotal</span>
            <span className="text-right">Confidence</span>
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
