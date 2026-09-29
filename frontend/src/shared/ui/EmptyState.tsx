import { Search } from 'lucide-react'
import { t } from '../lib/i18n'

export function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <Search size={24} />
      <h3>{t(title)}</h3>
      <p>{t(text)}</p>
    </div>
  )
}
