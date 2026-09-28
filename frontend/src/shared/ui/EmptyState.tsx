import { Search } from 'lucide-react'

export function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <Search size={24} />
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  )
}
