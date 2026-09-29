import type { GeoJSONSource, Map as MapLibreMap } from 'maplibre-gl'
import { nearbyHospitals } from './hospitalLocations'

export function hospitalFeatures(center: readonly [number, number]) {
  return {
    type: 'FeatureCollection' as const,
    features: nearbyHospitals(center).map((item) => ({
      type: 'Feature' as const,
      geometry: {
        type: 'Point' as const,
        coordinates: item.coordinates,
      },
      properties: { name: item.name, osmUrl: item.osmUrl, address: item.address },
    })),
  }
}

export function moveTo(map: MapLibreMap, center: readonly [number, number], zoom: number) {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  ;(map.getSource('medflow-hospitals') as GeoJSONSource | undefined)?.setData(
    hospitalFeatures(center),
  )
  map.easeTo({
    center: [...center],
    zoom,
    pitch: 55,
    bearing: -20,
    duration: reducedMotion ? 0 : 1100,
  })
}

export function addBuildings(map: MapLibreMap) {
  map.addSource('medflow-buildings', {
    type: 'vector',
    url: 'https://tiles.openfreemap.org/planet',
  })
  const firstLabel = map.getStyle().layers.find((layer) => layer.type === 'symbol')?.id
  map.addLayer(
    {
      id: 'medflow-3d-buildings',
      type: 'fill-extrusion',
      source: 'medflow-buildings',
      'source-layer': 'building',
      minzoom: 15,
      filter: ['!=', ['get', 'hide_3d'], true],
      paint: {
        'fill-extrusion-color': '#aab8af',
        'fill-extrusion-opacity': 0.84,
        'fill-extrusion-height': [
          'interpolate',
          ['linear'],
          ['zoom'],
          15,
          0,
          16,
          ['coalesce', ['get', 'render_height'], 8],
        ],
        'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
      },
    },
    firstLabel,
  )
}
