import { Activity } from 'lucide-react'

export function Brand() {
  return (
    <a className="public-brand" href="#welcome">
      <span className="brand-mark">
        <Activity size={25} />
      </span>
      <span>
        MedFlow<span>AI</span>
        <small>Госпитальная аналитика</small>
      </span>
    </a>
  )
}
