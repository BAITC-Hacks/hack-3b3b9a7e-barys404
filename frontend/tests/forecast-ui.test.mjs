import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { load } from './helpers/load.mjs'

const { hospitalDisplayName } = await load('src/entities/hospital/model/directory.ts')
const { ForecastsPage } = await load('src/pages/forecasts/ui/ForecastsPage.tsx')

test('short hospital labels keep distinguishing regions and do not change legal names', () => {
  const prefix = 'Государственное коммунальное предприятие на праве хозяйственного ведения '
  const names = ['Туркестанской', 'Карагандинской'].map(
    (region) =>
      `${prefix}"Областная клиническая больница" управления здравоохранения ${region} области`,
  )
  const labels = names.map(hospitalDisplayName)
  assert.notEqual(labels[0], labels[1])
  assert.ok(labels[0].includes('Туркестанской области'))
  assert.ok(labels[1].includes('Карагандинской области'))
  assert.equal(names[0].startsWith(prefix), true)
  assert.equal(hospitalDisplayName('Акционерное общество "Центр"'), '"Центр"')
  assert.equal(hospitalDisplayName('Городская больница №2'), 'Городская больница №2')
  assert.equal(hospitalDisplayName(''), '')
})

test('forecast heading names the task and repeats the selected hospital as requested', () => {
  const html = renderToStaticMarkup(
    createElement(ForecastsPage, { hospital: 'Hospital A', go: () => {} }),
  )
  assert.match(html, /Прогноз направлений/)
  assert.match(html, /role="tabpanel"/)
  assert.match(html, /aria-controls=/)
  assert.match(html, /Стационар: Hospital A/)
  assert.doesNotMatch(html, /Что покажет модель|Сменить стационар/)
})
