import type { LineItem } from '../types'
import ProductSearch from './ProductSearch'
import SOSelector from './SOSelector'

interface LineItemRowProps {
  item: LineItem
  index: number
  onUpdate: (index: number, updates: Partial<LineItem>) => void
}


export default function LineItemRow({ item, index, onUpdate }: LineItemRowProps) {
  return (
    <div className="grid grid-cols-[2fr_1fr_1fr_60px_80px] gap-2 items-center py-3 border-b border-white/5 last:border-0">
      {/* Description */}
      <div className="min-w-0">
        <p className="text-white text-sm leading-snug truncate">{item.description}</p>
        {item.sku && <p className="text-white/40 text-xs mt-0.5">SKU: {item.sku}</p>}
      </div>

      {/* Product match */}
      <div>
        <ProductSearch
          currentMatch={{
            odoo_id: item.product_odoo_id,
            name: item.product_name,
            confidence: item.product_confidence,
          }}
          alternatives={item.alternatives}
          onSelect={(odooId, name) =>
            onUpdate(index, {
              product_odoo_id: odooId || null,
              product_name: name === 'No match' ? null : name,
            })
          }
        />
      </div>

      {/* Sales Order */}
      <div>
        <SOSelector
          value={{ id: item.sales_order_id ?? null, name: item.sales_order_name ?? null }}
          onSelect={(id, name) =>
            onUpdate(index, {
              sales_order_id: id || null,
              sales_order_name: name || null,
            })
          }
          compact
        />
      </div>

      {/* Qty */}
      <div>
        <input
          type="number"
          min={0}
          step="any"
          value={item.quantity}
          onChange={e => onUpdate(index, { quantity: parseFloat(e.target.value) || 0 })}
          className="w-full bg-surface border border-white/20 text-white text-sm px-2 py-1 rounded focus:outline-none focus:border-primary text-right"
        />
      </div>

      {/* Unit price */}
      <div>
        <input
          type="number"
          min={0}
          step="any"
          value={item.unit_price}
          onChange={e => onUpdate(index, { unit_price: parseFloat(e.target.value) || 0 })}
          className="w-full bg-surface border border-white/20 text-white text-sm px-2 py-1 rounded focus:outline-none focus:border-primary text-right"
        />
      </div>
    </div>
  )
}
