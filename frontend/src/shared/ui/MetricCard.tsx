import { Activity } from 'lucide-react'

export function MetricCard({
  label,
  value,
  suffix,
  note,
  tone = 'plain',
  icon: Icon,
}: {
  label: string
  value: string
  suffix?: string
  note?: string
  tone?: 'plain' | 'accent'
  icon: typeof Activity
}) {
  return (
    <div className={`metric-card ${tone === 'accent' ? 'metric-accent' : ''}`}>
      <div className="metric-top">
        <span>{label}</span>
        <Icon size={18} strokeWidth={1.7} />
      </div>
      <div className="metric-value">
        {value}
        <small>{suffix}</small>
      </div>
      {note && <div className="metric-note">{note}</div>}
    </div>
  )
}
