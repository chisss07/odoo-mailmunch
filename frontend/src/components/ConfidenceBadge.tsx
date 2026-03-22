interface ConfidenceBadgeProps {
  confidence: string
}

const CONFIG: Record<string, { dot: string; label: string; text: string }> = {
  high: {
    dot: 'bg-green-400',
    label: 'High',
    text: 'text-green-400',
  },
  medium: {
    dot: 'bg-yellow-400',
    label: 'Medium',
    text: 'text-yellow-400',
  },
  low: {
    dot: 'bg-red-400',
    label: 'Low',
    text: 'text-red-400',
  },
}

export default function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  const key = confidence.toLowerCase()
  const config = CONFIG[key] ?? { dot: 'bg-white/30', label: confidence, text: 'text-white/50' }

  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-full flex-shrink-0 ${config.dot}`} />
      <span className={`text-xs ${config.text}`}>{config.label}</span>
    </span>
  )
}
