import { Activity } from 'lucide-react'
import { t } from '../lib/i18n'

export function Brand() {
  return (
    <a className="public-brand" href="#welcome">
      <span className="brand-mark">
        <Activity size={25} />
      </span>
      <span>
        MedFlow<span>AI</span>
        <small>{t('Госпитальная аналитика')}</small>
      </span>
    </a>
  )
}
