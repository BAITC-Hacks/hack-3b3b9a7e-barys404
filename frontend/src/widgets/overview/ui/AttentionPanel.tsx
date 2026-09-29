import { t } from '../../../shared/lib/i18n'
import { ArrowUpRight } from 'lucide-react'
import type { Overview } from '../../../shared/api/types'
import { decimal, number } from '../../../shared/lib/format'

export function AttentionPanel({
  items,
  openHospital,
}: {
  items: Overview['attention']
  openHospital: (name: string) => void
}) {
  return (
    <section className="panel attention-panel">
      <div className="panel-heading">
        <div>
          <h2>{t('Рост направлений')}</h2>
          <p>{t('Последние два полных периода по 7 дней')}</p>
        </div>
      </div>
      {items.length ? (
        <div className="attention-list">
          {items.map((item) => (
            <button
              key={item.hospital}
              onClick={() => openHospital(item.hospital)}
              className="attention-item"
              title={item.hospital}
            >
              <span className="attention-arrow">
                <ArrowUpRight size={17} />
              </span>
              <span className="attention-text">
                <strong>{item.hospital}</strong>
                <span className="attention-meta">
                  <small>
                    {number(item.previous)} → {number(item.current)} {t('направлений')}{' '}
                  </small>
                  <b>+{decimal(item.change_pct, 0)}%</b>
                </span>
              </span>
            </button>
          ))}
        </div>
      ) : (
        <div className="quiet-state">
          {t('За этот период нет роста с достаточным числом наблюдений.')}
        </div>
      )}
      <div className="panel-footnote">
        {t(
          'Рост записанного потока — повод проверить данные и ситуацию, а не оценка занятости коек.',
        )}{' '}
      </div>
    </section>
  )
}
