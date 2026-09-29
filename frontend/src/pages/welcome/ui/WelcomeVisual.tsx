import { t } from '../../../shared/lib/i18n'
import { Activity, Clock3, ShieldCheck, TrendingUp } from 'lucide-react'
import { useId } from 'react'
import { useEntrance } from '../../../shared/lib/useEntrance'

export function WelcomeVisual() {
  const id = useId()
  const reveal = useEntrance<SVGRectElement>(undefined, 'draw')
  return (
    <div className="welcome-visual" aria-label={t('Иллюстрация аналитического кабинета')}>
      <div className="visual-top">
        <span>
          <i /> {t('MedFlow · Обзор')}{' '}
        </span>
        <span>{t('Иллюстрация')}</span>
      </div>
      <div className="visual-heading">{t('Направления и ожидание')}</div>
      <div className="visual-metrics">
        <span>
          <Activity size={18} />
          <small>{t('Направления')}</small>
          <b>{t('Динамика потока')}</b>
        </span>
        <span>
          <Clock3 size={18} />
          <small>{t('Ожидание')}</small>
          <b>{t('История и оценка')}</b>
        </span>
      </div>
      <div className="visual-chart">
        <div>
          <span>{t('Поступление направлений')}</span>
          <TrendingUp size={17} />
        </div>
        <svg
          viewBox="0 0 460 150"
          role="img"
          aria-label={t('Условный график потока, не реальные данные')}
        >
          <defs>
            <clipPath id={`${id}-reveal`}>
              <rect
                ref={reveal}
                width="460"
                height="150"
                style={{ transformOrigin: '0 0', transformBox: 'view-box' }}
              />
            </clipPath>
          </defs>
          <path d="M0 30 H460 M0 75 H460 M0 120 H460" className="visual-grid" />
          <g clipPath={`url(#${id}-reveal)`}>
            <path
              d="M0 120 L55 105 L110 114 L165 65 L220 82 L275 35 L330 53 L390 20 L460 38 V150 H0Z"
              className="visual-area"
            />
            <path
              d="M0 120 L55 105 L110 114 L165 65 L220 82 L275 35 L330 53 L390 20 L460 38"
              fill="none"
              className="visual-line"
              strokeWidth="3"
            />
          </g>
        </svg>
        <small>{t('История → тенденции → прогноз')}</small>
      </div>
      <div className="visual-bottom">
        <ShieldCheck size={16} /> {t('Каждый сотрудник видит разрешённые ему данные')}{' '}
      </div>
    </div>
  )
}
