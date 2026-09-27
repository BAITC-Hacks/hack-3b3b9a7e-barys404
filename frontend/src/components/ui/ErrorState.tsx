import { Info } from 'lucide-react'

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="message message-error">
      <Info size={18} />
      <span>{message}</span>
    </div>
  )
}
