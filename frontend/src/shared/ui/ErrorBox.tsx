import { Info } from 'lucide-react'
import { t } from '../lib/i18n'

export function ErrorBox({ text }: { text: string }) {
  return text ? (
    <div className="message message-error" role="alert">
      <Info size={18} />
      {t(text)}
    </div>
  ) : null
}
