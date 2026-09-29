import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { load } from './helpers/load.mjs'

const { REGION_NAMES, regionLabel } = await load('src/entities/region/model/regions.ts')
const { FilterBar } = await load('src/features/filter-referrals/ui/FilterBar.tsx')
const { editFilterDraft, initialFilters } = await load(
  'src/features/filter-referrals/model/filterDraft.ts',
)
const { query } = await load('src/shared/api/client.ts')

test('all 20 region codes have labels; unknown codes remain visible without guessing', () => {
  const codes = [
    '10',
    '11',
    '15',
    '19',
    '23',
    '27',
    '31',
    '33',
    '35',
    '39',
    '43',
    '47',
    '55',
    '59',
    '61',
    '62',
    '63',
    '71',
    '75',
    '79',
  ]
  assert.deepEqual(Object.keys(REGION_NAMES), codes)
  for (const code of codes) assert.equal(regionLabel(code), `${REGION_NAMES[code]} · ${code}`)
  assert.equal(regionLabel('31'), 'Жамбылская область · 31')
  assert.equal(regionLabel('75'), 'г. Алматы · 75')
  assert.equal(regionLabel(''), 'Все регионы')
  assert.equal(regionLabel('99'), 'Регион · 99')
  assert.equal(regionLabel('toString'), 'Регион · toString')
})

test('the shared overview filter displays names but selects, sends and resets original codes', () => {
  const filters = { start: '2025-01-01', end: '2025-03-31', region: '31', profile: 'profile' }
  const bootstrap = {
    period: { start: filters.start, end: filters.end },
    regions: ['31', '75', '99'],
    profiles: ['profile'],
  }
  const props = {
    filters,
    bootstrap,
    setFilters: () => {
      throw new Error('Rendering must not apply filters')
    },
  }
  const html = renderToStaticMarkup(createElement(FilterBar, props))
  assert.match(html, /<fieldset class="filter-period">/)
  assert.match(html, /Период регистрации/)
  assert.match(html, /type="date"[^>]*min="2025-01-01"[^>]*max="2025-03-31"/)
  assert.match(html, /value="31" selected="">Жамбылская область · 31/)
  assert.match(html, /value="75">г\. Алматы · 75/)
  assert.match(html, /value="99">Регион · 99/)
  assert.match(html, /<form[^>]*aria-label="Фильтры направлений"/)
  assert.match(html, /type="submit" disabled=""/)
  const next = editFilterDraft(filters, 'region', '75')
  assert.deepEqual(next, { ...filters, region: '75' })
  assert.equal(filters.region, '31')
  assert.equal(new URLSearchParams(query(next)).get('region'), '75')
  assert.deepEqual(initialFilters(bootstrap.period), {
    start: filters.start,
    end: filters.end,
    region: '',
    profile: '',
  })
  assert.equal(editFilterDraft(filters, 'start', '2025-04-01').end, '2025-04-01')
  assert.equal(editFilterDraft(filters, 'end', '2024-12-31').start, '2024-12-31')
  assert.equal(editFilterDraft(filters, 'start', '').end, filters.end)
})
