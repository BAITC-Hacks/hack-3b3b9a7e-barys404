import { t } from '../lib/i18n'

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string
  title: string
  description: string
  action?: React.ReactNode
}) {
  return (
    <div className="page-heading">
      <div className="page-heading-copy">
        {eyebrow && <div className="eyebrow">{t(eyebrow)}</div>}
        <h1>{t(title)}</h1>
        <p>{t(description)}</p>
      </div>
      {action && <div className="page-heading-action">{action}</div>}
    </div>
  )
}
