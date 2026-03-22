import type { TrackingInfo } from '../types'

interface TrackingPanelProps {
  tracking: TrackingInfo | null
}

function carrierTrackingUrl(number: string, carrierUrl: string): string {
  if (carrierUrl) return carrierUrl
  // Fallback heuristics if no URL is provided
  const upper = number.toUpperCase()
  if (/^1Z/.test(upper)) {
    return `https://www.ups.com/track?tracknum=${number}`
  }
  if (/^\d{20,22}$/.test(upper)) {
    return `https://www.fedex.com/fedextrack/?tracknumbers=${number}`
  }
  if (/^\d{22}$/.test(upper) || /^92/.test(number)) {
    return `https://tools.usps.com/go/TrackConfirmAction?tLabels=${number}`
  }
  return `https://www.google.com/search?q=track+package+${number}`
}

export default function TrackingPanel({ tracking }: TrackingPanelProps) {
  if (!tracking || tracking.tracking_numbers.length === 0) {
    return (
      <div className="bg-surface-light rounded-lg p-4">
        <h3 className="text-white/50 text-xs uppercase tracking-wider font-medium mb-3">
          Tracking
        </h3>
        <p className="text-white/30 text-sm">No tracking information available</p>
      </div>
    )
  }

  return (
    <div className="bg-surface-light rounded-lg p-4">
      <h3 className="text-white/50 text-xs uppercase tracking-wider font-medium mb-3">
        Tracking
      </h3>

      <div className="space-y-3">
        {tracking.tracking_numbers.map((t, i) => {
          const href = carrierTrackingUrl(t.number, t.url)
          return (
            <div key={i} className="flex items-center justify-between gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-white/40 text-xs capitalize mb-0.5">{t.carrier || 'Carrier'}</p>
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary text-sm hover:underline font-mono truncate block"
                  aria-label={`Track ${t.number} with ${t.carrier}`}
                >
                  {t.number}
                </a>
              </div>
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-white/30 hover:text-primary flex-shrink-0 transition-colors"
                aria-label="Open tracking link"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
              </a>
            </div>
          )
        })}
      </div>

      {tracking.estimated_delivery && (
        <div className="mt-4 pt-3 border-t border-white/10">
          <p className="text-white/40 text-xs uppercase tracking-wider mb-1">
            Estimated Delivery
          </p>
          <p className="text-white/80 text-sm">
            {new Date(tracking.estimated_delivery).toLocaleDateString(undefined, {
              weekday: 'short',
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            })}
          </p>
        </div>
      )}
    </div>
  )
}
