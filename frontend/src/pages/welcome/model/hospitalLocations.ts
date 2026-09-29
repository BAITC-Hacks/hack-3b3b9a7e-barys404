import coordinates from './hospitalCoordinates.json'

export const localities = [
  { id: 'astana', name: 'Астана', center: [71.4304, 51.1282] },
  { id: 'almaty', name: 'Алматы', center: [76.945, 43.2389] },
  { id: 'shymkent', name: 'Шымкент', center: [69.5967, 42.3417] },
  { id: 'aktobe', name: 'Актобе', center: [57.166, 50.2839] },
  { id: 'karaganda', name: 'Караганда', center: [73.085, 49.806] },
  { id: 'kostanay', name: 'Костанай', center: [63.624, 53.214] },
  { id: 'pavlodar', name: 'Павлодар', center: [76.967, 52.287] },
  { id: 'petropavl', name: 'Петропавловск', center: [69.15, 54.872] },
  { id: 'kokshetau', name: 'Кокшетау', center: [69.377, 53.284] },
  { id: 'oral', name: 'Уральск', center: [51.37, 51.222] },
  { id: 'atyrau', name: 'Атырау', center: [51.92, 47.106] },
  { id: 'aktau', name: 'Актау', center: [51.168, 43.652] },
  { id: 'kyzylorda', name: 'Кызылорда', center: [65.482, 44.848] },
  { id: 'taraz', name: 'Тараз', center: [71.365, 42.9] },
  { id: 'taldykorgan', name: 'Талдыкорган', center: [78.373, 45.014] },
  { id: 'semey', name: 'Семей', center: [80.227, 50.411] },
  { id: 'oskemen', name: 'Усть-Каменогорск', center: [82.628, 49.948] },
  { id: 'turkestan', name: 'Туркестан', center: [68.272, 43.298] },
  { id: 'zhezkazgan', name: 'Жезказган', center: [67.71, 47.803] },
] as const

export type LocalityId = (typeof localities)[number]['id']

export type HospitalLocation = {
  id: string
  name: string
  coordinates: [number, number]
  osmName: string
  osmUrl: string
  address: string
}

export const locatedHospitals: HospitalLocation[] = coordinates.map((item) => ({
  id: item.osm_id,
  name: item.name,
  coordinates: item.coordinates as [number, number],
  osmName: item.osm_name,
  osmUrl: `https://www.openstreetmap.org/${item.osm_id}`,
  address: item.address,
}))

export function nearbyHospitals(center: readonly [number, number], radiusKm = 25) {
  const latitude = (center[1] * Math.PI) / 180
  return locatedHospitals.filter((hospital) => {
    const latitudeDistance = (hospital.coordinates[1] - center[1]) * 111
    const longitudeDistance =
      (hospital.coordinates[0] - center[0]) * 111 * Math.cos(latitude)
    return Math.hypot(latitudeDistance, longitudeDistance) <= radiusKm
  })
}
