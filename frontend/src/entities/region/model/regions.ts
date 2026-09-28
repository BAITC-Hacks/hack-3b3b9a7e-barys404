// Regional prefixes of KATO codes. Display only: never replace API filter values.
// Source: https://adilet.zan.kz/rus/docs/G26G0000256
export const REGION_NAMES: Readonly<Record<string, string>> = Object.freeze({
  '10': 'Область Абай',
  '11': 'Акмолинская область',
  '15': 'Актюбинская область',
  '19': 'Алматинская область',
  '23': 'Атырауская область',
  '27': 'Западно-Казахстанская область',
  '31': 'Жамбылская область',
  '33': 'Область Жетісу',
  '35': 'Карагандинская область',
  '39': 'Костанайская область',
  '43': 'Кызылординская область',
  '47': 'Мангистауская область',
  '55': 'Павлодарская область',
  '59': 'Северо-Казахстанская область',
  '61': 'Туркестанская область',
  '62': 'Область Ұлытау',
  '63': 'Восточно-Казахстанская область',
  '71': 'г. Астана',
  '75': 'г. Алматы',
  '79': 'г. Шымкент',
})

export function regionLabel(code: string): string {
  if (!code) return 'Все регионы'
  const name = Object.hasOwn(REGION_NAMES, code) ? REGION_NAMES[code] : 'Регион'
  return `${name} · ${code}`
}
