import type { GeoJSONSource, Map as MapLibreMap } from 'maplibre-gl'
import { t } from '../../../shared/lib/i18n'
import { addBuildings, hospitalFeatures } from './cityMapData'

export function addCityLayers(
  map: MapLibreMap,
  maplibre: typeof import('maplibre-gl'),
  center: readonly [number, number],
) {
  addBuildings(map)
  map.addSource('medflow-hospitals', {
    type: 'geojson',
    data: hospitalFeatures(center),
    cluster: true,
    clusterRadius: 36,
    clusterMaxZoom: 16,
  })
  map.addLayer({
    id: 'medflow-hospital-clusters',
    type: 'circle',
    source: 'medflow-hospitals',
    filter: ['has', 'point_count'],
    paint: {
      'circle-color': '#14877c',
      'circle-radius': ['step', ['get', 'point_count'], 16, 20, 21, 60, 25],
      'circle-stroke-color': '#fff',
      'circle-stroke-width': 2,
    },
  })
  map.addLayer({
    id: 'medflow-hospital-count',
    type: 'symbol',
    source: 'medflow-hospitals',
    filter: ['has', 'point_count'],
    layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-size': 12 },
    paint: { 'text-color': '#fff' },
  })
  map.addLayer({
    id: 'medflow-hospital-points',
    type: 'circle',
    source: 'medflow-hospitals',
    filter: ['!', ['has', 'point_count']],
    paint: {
      'circle-color': '#f5a33b',
      'circle-radius': 7,
      'circle-stroke-color': '#fff',
      'circle-stroke-width': 2,
    },
  })

  map.on('click', 'medflow-hospital-clusters', (event) => {
    const feature = map.queryRenderedFeatures(event.point, {
      layers: ['medflow-hospital-clusters'],
    })[0]
    const clusterId = feature?.properties?.cluster_id
    if (clusterId == null) return
    const source = map.getSource('medflow-hospitals') as GeoJSONSource
    void source.getClusterExpansionZoom(clusterId).then((zoom) => {
      if (feature.geometry.type !== 'Point') return
      map.easeTo({ center: feature.geometry.coordinates as [number, number], zoom })
    })
  })
  map.on('click', 'medflow-hospital-points', (event) => {
    const feature = event.features?.[0]
    if (!feature || feature.geometry.type !== 'Point') return
    const content = document.createElement('div')
    content.className = 'welcome-hospital-popup'
    const title = document.createElement('strong')
    title.textContent = String(feature.properties?.name ?? '')
    const note = document.createElement('span')
    note.textContent = String(feature.properties?.address || t('Координаты объекта OpenStreetMap'))
    const source = document.createElement('a')
    source.href = String(feature.properties?.osmUrl ?? 'https://www.openstreetmap.org/copyright')
    source.target = '_blank'
    source.rel = 'noopener noreferrer'
    source.textContent = t('Открыть в OpenStreetMap')
    content.append(title, note, source)
    new maplibre.Popup({ offset: 12 })
      .setLngLat(feature.geometry.coordinates as [number, number])
      .setDOMContent(content)
      .addTo(map)
  })
  for (const layer of ['medflow-hospital-clusters', 'medflow-hospital-points']) {
    map.on('mouseenter', layer, () => {
      map.getCanvas().style.cursor = 'pointer'
    })
    map.on('mouseleave', layer, () => {
      map.getCanvas().style.cursor = ''
    })
  }
}
