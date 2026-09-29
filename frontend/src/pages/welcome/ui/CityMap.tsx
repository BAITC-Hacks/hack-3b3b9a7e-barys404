import { useEffect, useRef, useState } from 'react'
import type { Map as MapLibreMap } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import { MapPin, RotateCcw } from 'lucide-react'
import { t } from '../../../shared/lib/i18n'
import { moveTo } from '../model/cityMapData'
import { addCityLayers } from '../model/cityMapLayers'

type MapStatus = 'loading' | 'ready' | 'error'

export function CityMap({
  center,
  zoom,
}: {
  center: readonly [number, number]
  zoom: number
}) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const centerRef = useRef(center)
  const zoomRef = useRef(zoom)
  const [status, setStatus] = useState<MapStatus>('loading')
  const [attempt, setAttempt] = useState(0)
  centerRef.current = center
  zoomRef.current = zoom

  useEffect(() => {
    let disposed = false
    let loaded = false
    let map: MapLibreMap | null = null
    setStatus('loading')

    async function initialize() {
      try {
        const [maplibre] = await Promise.all([
          import('maplibre-gl'),
          import('maplibre-gl/dist/maplibre-gl.css'),
        ])
        if (disposed || !canvasRef.current) return

        maplibre.setWorkerUrl(workerUrl)
        map = new maplibre.Map({
          container: canvasRef.current,
          style: 'https://tiles.openfreemap.org/styles/positron',
          center: [...centerRef.current],
          zoom: zoomRef.current,
          pitch: 55,
          bearing: -20,
          canvasContextAttributes: { antialias: true },
        })
        const activeMap = map
        mapRef.current = activeMap
        activeMap.scrollZoom.disable()
        activeMap.addControl(new maplibre.NavigationControl({ showCompass: true }), 'bottom-right')
        activeMap.on('load', () => {
          if (disposed) return
          try {
            addCityLayers(activeMap, maplibre, centerRef.current)
            loaded = true
            setStatus('ready')
          } catch {
            setStatus('error')
          }
        })
        activeMap.on('error', () => {
          if (!disposed && !loaded) setStatus('error')
        })
      } catch {
        if (!disposed) setStatus('error')
      }
    }

    void initialize()
    return () => {
      disposed = true
      mapRef.current = null
      map?.remove()
    }
  }, [attempt])

  useEffect(() => {
    if (status === 'ready' && mapRef.current) moveTo(mapRef.current, center, zoom)
  }, [center, zoom, status])

  return (
    <>
      <div
        ref={canvasRef}
        className="welcome-map-canvas"
        aria-label={t('Интерактивная карта города')}
      />
      {status !== 'ready' && (
        <div className="welcome-map-overlay" role={status === 'error' ? 'alert' : 'status'}>
          <MapPin size={22} aria-hidden="true" />
          <span>
            {status === 'error' ? t('Карта сейчас недоступна.') : t('Загружаем карту города…')}
          </span>
          {status === 'error' && (
            <button type="button" onClick={() => setAttempt((value) => value + 1)}>
              <RotateCcw size={15} aria-hidden="true" /> {t('Повторить')}
            </button>
          )}
        </div>
      )}
    </>
  )
}
