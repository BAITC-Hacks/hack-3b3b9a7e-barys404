import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { build } from 'esbuild'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

// Render the real components without a browser. This checks visible data and
// labels; it deliberately does not claim layout, interaction or visual coverage.
const compiled = await build({
  absWorkingDir: fileURLToPath(new URL('..', import.meta.url)),
  entryPoints: ['src/App.tsx'], bundle: true, packages: 'external',
  platform: 'node', format: 'cjs', write: false, logLevel: 'silent',
})
const module = { exports: {} }
new Function('require', 'module', 'exports', compiled.outputFiles[0].text)(createRequire(import.meta.url), module, module.exports)
const { WeeklyTrend, ModelQuality, OutcomeBreakdown } = module.exports
const render = (component, props) => renderToStaticMarkup(createElement(component, props))

test('partial week count is visible but excluded from the full-week chart', () => {
  const html = render(WeeklyTrend, { rows: [
    { week: '2025-03-24', referrals: 41653, period_start: '2025-03-24', period_end: '2025-03-30', days_in_period: 7, partial_week: false },
    { week: '2025-03-31', referrals: 15183, period_start: '2025-03-31', period_end: '2025-03-31', days_in_period: 1, partial_week: true },
  ] })
  const chart = html.match(/<svg[\s\S]*?<\/svg>/)?.[0]
  assert.ok(chart)
  assert.match(chart, /aria-label="24 мар/)
  assert.match(chart, /41[\s\u00a0\u202f]653/)
  assert.doesNotMatch(chart, /15[\s\u00a0\u202f]183/)
  assert.match(html, /15[\s\u00a0\u202f]183/)
  assert.match(html, /1 из 7 дней/)
})

test('a period containing only a partial week explains absence of a full-week chart', () => {
  const html = render(WeeklyTrend, { rows: [
    { week: '2025-03-31', referrals: 42, period_start: '2025-03-31', period_end: '2025-04-01', days_in_period: 2, partial_week: true },
  ] })
  assert.match(html, /Нет полных календарных недель/)
  assert.match(html, /42 направл/)
  assert.match(html, /2 из 7 дней/)
  assert.doesNotMatch(html, /aria-label="График направлений/)
})

test('all outcome categories contribute to the total and a zero has no invented bar', () => {
  const html = render(OutcomeBreakdown, { stats: {
    referrals: 20, hospitalized: 10, refused: 5, unresolved: 0, invalid_outcome: 4, conflicting: 1,
  } })
  assert.match(html, /Некорректные \/ конфликтующие/)
  assert.match(html, /outcome-fill amber" style="width:25%"/)
  assert.match(html, /outcome-fill gray" style="width:0%"/)
  assert.match(html, /Все категории входят в 20 направлений/)
})

test('stale metrics never render as current quality even if a response retains old numbers', () => {
  const props = { name: 'Ожидание', unit: 'дня', baseline: 'Baseline', evidence: {
    status: { available: false, stale: true, reason: 'Old model' }, model_version: 'test-v2',
    test_period: { start: '2025-03-14', end: '2025-03-31' },
    metrics: { mae: 123.45, baseline_mae: 234.56, rmse: 345.67 },
  } }
  const html = render(ModelQuality, props)
  assert.match(html, /Модель недоступна/)
  assert.match(html, /test-v2/)
  assert.doesNotMatch(html, /123|234|345/)
  props.evidence.status = { available: true, stale: false, reason: 'Ready' }
  const current = render(ModelQuality, props)
  assert.match(current, /Метрики актуальны/)
  assert.match(current, /123,45/)
  assert.match(current, /14 мар[^<]*2025/)
  assert.match(current, /31 мар[^<]*2025/)
})
