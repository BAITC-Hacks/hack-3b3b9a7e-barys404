import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { load } from './helpers/load.mjs'

const { durationParts } = await load('src/shared/lib/duration.ts')
const { WaitEstimateCard } = await load('src/widgets/forecasts/ui/WaitEstimateCard.tsx')
const text = (value) =>
  durationParts(value)
    .map(({ value, unit }) => `${value} ${unit}`)
    .join(' ')

test('waiting duration uses minutes, hours or days, carrying rounded boundaries and omitting zero parts', () => {
  for (const [days, expected] of [
    [0.1, '2 ч 24 мин'],
    [0.5, '12 ч'],
    [1.5, '1 д 12 ч'],
    [3, '3 д'],
    [30 / 1440, '30 мин'],
    [1 / 24, '1 ч'],
    [1, '1 д'],
    [0.999999, '1 д'],
    [1.999999, '2 д'],
    [0.0001, '<1 мин'],
    [0, '0 мин'],
  ])
    assert.equal(text(days), expected)
  for (const invalid of [null, undefined, -0.1, NaN, Infinity])
    assert.deepEqual(durationParts(invalid), [])
})

test('the actual forecast card displays the duration without changing prediction or masking missing results', () => {
  const result = {
    clipped: false,
    prediction: 0.1,
    method: 'catboost',
    support: 10,
    group_quality: null,
    mae: 5.27,
  }
  const html = renderToStaticMarkup(createElement(WaitEstimateCard, { result }))
  assert.match(html, /aria-label="2 ч 24 мин"/)
  assert.doesNotMatch(html, /0,1|около/i)
  assert.match(html, /5,27 дня/)
  assert.equal(result.prediction, 0.1)
  // Both reported hospital/profile examples use the same presentation path.
  for (const [minutes, expected] of [
    [49, '49 мин'],
    [16, '16 мин'],
  ]) {
    const group = renderToStaticMarkup(
      createElement(WaitEstimateCard, {
        result: { ...result, method: 'hospital_profile_median', prediction: minutes / 1440 },
      }),
    )
    assert.ok(group.includes(`aria-label="${expected}"`))
    assert.doesNotMatch(group, /&lt;0,1/)
  }
  const unavailable = renderToStaticMarkup(
    createElement(WaitEstimateCard, { result: { ...result, clipped: true, prediction: null } }),
  )
  assert.match(unavailable, /Оценка недоступна/)
  assert.doesNotMatch(unavailable, /0 мин|2 ч/)
})
