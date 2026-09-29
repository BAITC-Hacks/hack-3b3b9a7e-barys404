import { t } from '../../../shared/lib/i18n'
import type { Overview } from '../../../shared/api/types'
import { number } from '../../../shared/lib/format'
import { useStaggeredEntrance } from '../../../shared/lib/useEntrance'
export function OutcomeBreakdown({ stats }: { stats: Overview['stats'] }) {
  const bars = useStaggeredEntrance<HTMLDivElement>(stats, 'grow', '.outcome-fill')
  return (
    <section className="panel outcome-panel">
      <div className="panel-heading">
        <div>
          <h2>{t('Исходы направлений')}</h2>
          <p>{t('По записям в выгрузке')}</p>
        </div>
      </div>
      <div className="outcome-stack" ref={bars}>
        {[
          [t('Госпитализации'), stats.hospitalized, 'teal'],
          [t('Отказы'), stats.refused, 'coral'],
          [t('Исход не записан'), stats.unresolved, 'gray'],
        ].map(([label, value, color]) => (
          <div className="outcome-row" key={String(label)}>
            <span>{label}</span>
            <div className="outcome-track">
              <i
                className={`outcome-fill ${color}`}
                style={{
                  width: `${(Number(value) / Math.max(1, stats.referrals)) * 100}%`,
                }}
              />
            </div>
            <strong>{number(Number(value))}</strong>
          </div>
        ))}
      </div>
      <p className="panel-footnote">
        {t('Отсутствие исхода в выгрузке не означает, что человек ожидает сейчас.')}{' '}
      </p>
    </section>
  )
}
