import { useState } from 'react'
import { t } from '../../../shared/lib/i18n'
import { localities, locatedHospitals, nearbyHospitals } from '../model/hospitalLocations'
import type { HospitalLocation, LocalityId } from '../model/hospitalLocations'
import { CityMap } from './CityMap'
import { CountryMap } from './CountryMap'

type Selection =
  | { kind: 'country' }
  | { kind: 'city'; locality: LocalityId }
  | { kind: 'hospital'; hospital: HospitalLocation }

const featuredLocalities = localities.slice(0, 3)

export function WelcomeMap() {
  const [selected, setSelected] = useState<Selection>({ kind: 'country' })
  const selectedLocality = selected.kind === 'city'
    ? localities.find((item) => item.id === selected.locality)
    : undefined
  const center = selected.kind === 'hospital'
    ? selected.hospital.coordinates
    : selectedLocality?.center
  const selectedCount = center ? nearbyHospitals(center).length : locatedHospitals.length

  return (
    <section className="welcome-map" aria-labelledby="welcome-map-title">
      <div className="welcome-map-header">
        <div>
          <span className="public-eyebrow">{t('География')}</span>
          <h2 id="welcome-map-title">{t('Стационары на карте Казахстана')}</h2>
          <p>{t('На карте показаны организации, сопоставленные с объектами OpenStreetMap. Выберите город или больницу для просмотра в 3D.')}</p>
        </div>
        <div className="welcome-map-locations" role="group" aria-label={t('Выбор города')}>
          <button
            type="button"
            className={selected.kind === 'country' ? 'is-selected' : ''}
            aria-pressed={selected.kind === 'country'}
            onClick={() => setSelected({ kind: 'country' })}
          >
            {t('Весь Казахстан')}
          </button>
          {featuredLocalities.map((locality) => (
            <button
              type="button"
              key={locality.id}
              className={selected.kind === 'city' && selected.locality === locality.id ? 'is-selected' : ''}
              aria-pressed={selected.kind === 'city' && selected.locality === locality.id}
              onClick={() => setSelected({ kind: 'city', locality: locality.id })}
            >
              {t(locality.name)}
            </button>
          ))}
        </div>
      </div>

      <div className="welcome-map-stage">
        {selected.kind === 'country' ? (
          <CountryMap
            onSelectCity={(locality) => setSelected({ kind: 'city', locality })}
            onSelectHospital={(hospital) => setSelected({ kind: 'hospital', hospital })}
          />
        ) : (
          center && <CityMap center={center} zoom={selected.kind === 'hospital' ? 16 : 11.5} />
        )}
      </div>

      <div className="welcome-map-footer">
        <span>
          {selected.kind === 'hospital' && <strong>{selected.hospital.osmName}. </strong>}
          {selected.kind === 'country'
            ? t('{count} из 1 382 организаций сопоставлены с точками OpenStreetMap. Остальные не показаны.', {
                count: selectedCount,
              })
            : t('Сопоставленных организаций поблизости: {count}.', {
                count: selectedCount,
              })}
        </span>
        <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
          © OpenStreetMap contributors
        </a>
      </div>
    </section>
  )
}
