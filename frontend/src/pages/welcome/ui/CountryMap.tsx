import { useState } from 'react'
import { t } from '../../../shared/lib/i18n'
import { localities, locatedHospitals } from '../model/hospitalLocations'
import type { HospitalLocation, LocalityId } from '../model/hospitalLocations'
import { kazakhstanOutline } from '../model/kazakhstanOutline'

function project(coordinates: readonly [number, number]): [number, number] {
  return [
    ((coordinates[0] - 46.492161) / (87.3156316 - 46.492161)) * 1000,
    ((55.4804002 - coordinates[1]) / (55.4804002 - 40.5686476)) * 550,
  ]
}

export function CountryMap({
  onSelectCity,
  onSelectHospital,
}: {
  onSelectCity: (location: LocalityId) => void
  onSelectHospital: (hospital: HospitalLocation) => void
}) {
  const [hovered, setHovered] = useState<HospitalLocation | null>(null)

  return (
    <div className="welcome-country-map">
      <svg
        viewBox="0 0 1000 550"
        role="img"
        aria-label={t('Контур Казахстана с точками организаций')}
      >
        <defs>
          <clipPath id="welcome-kazakhstan-clip">
            <path d={kazakhstanOutline} />
          </clipPath>
        </defs>
        <path d={kazakhstanOutline} className="welcome-country-outline" />
        {localities.map((locality) => {
          const [x, y] = project(locality.center)
          return (
            <g
              key={locality.id}
              className="welcome-country-city"
              role="button"
              tabIndex={0}
              aria-label={t('Открыть 3D-карту города {city}', { city: t(locality.name) })}
              onClick={() => onSelectCity(locality.id)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  onSelectCity(locality.id)
                }
              }}
            >
              <circle cx={x} cy={y} r="8" className="welcome-country-city-hit" />
              <circle cx={x} cy={y} r="3.5" className="welcome-country-city-dot" />
            </g>
          )
        })}
        <g clipPath="url(#welcome-kazakhstan-clip)">
          {locatedHospitals.map((hospital) => {
            const [x, y] = project(hospital.coordinates)
            return (
              <circle
                key={hospital.id}
                className="welcome-country-hospital"
                role="button"
                tabIndex={0}
                aria-label={hospital.name}
                cx={x}
                cy={y}
                r="2.7"
                onMouseEnter={() => setHovered(hospital)}
                onMouseLeave={() => setHovered(null)}
                onFocus={() => setHovered(hospital)}
                onBlur={() => setHovered(null)}
                onClick={() => onSelectHospital(hospital)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    onSelectHospital(hospital)
                  }
                }}
              >
                <title>{hospital.name}</title>
              </circle>
            )
          })}
        </g>
      </svg>
      {hovered && (
        <div className="welcome-country-tooltip">
          <strong>{hovered.name}</strong>
          {hovered.address && <span>{hovered.address}</span>}
          <small>{t('Координаты объекта OpenStreetMap')}</small>
        </div>
      )}
      <div className="welcome-country-hint">{t('Нажмите на точку или выберите город')}</div>
    </div>
  )
}
