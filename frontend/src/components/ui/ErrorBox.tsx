import { Info } from 'lucide-react'

export function ErrorBox({ text }: { text: string }) {
  return text ? (
    <div className="message message-error" role="alert">
      <Info size={18} />
      {text}
    </div>
  ) : null
}
