import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { build } from 'esbuild'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

async function load(entry) {
  const result = await build({ absWorkingDir: fileURLToPath(new URL('..', import.meta.url)),
    entryPoints: [entry], bundle: true, packages: 'external', platform: 'node', format: 'cjs', write: false, logLevel: 'silent' })
  const module = { exports: {} }
  new Function('require', 'module', 'exports', result.outputFiles[0].text)(createRequire(import.meta.url), module, module.exports)
  return module.exports
}
const { BriefingPanel, BriefingReview } = await load('src/WorkspacePages.tsx')
const api = await load('src/api.ts')
const render = (component, props) => renderToStaticMarkup(createElement(component, props))

test('a new briefing cannot download until preview and review', () => {
  const html = render(BriefingPanel, { filters: { start: '2025-01-01', end: '2025-03-31', region: '', profile: '' }, hospitals: ['Hospital A'] })
  assert.match(html, /Подготовить просмотр/)
  assert.match(html, /<button class="primary-button" disabled=""[^>]*>[\s\S]*?Скачать PDF-сводку/)
  assert.match(html, /01\.01\.2025 — 31\.03\.2025/)
  assert.doesNotMatch(html, /type="checkbox"/)
})

test('review shows suppressed values, evidence period and explicit human acknowledgement', () => {
  const props = { confirmed: false, change: () => {}, preview: {
    snapshot: { minimum_group_size: 30, review_question: 'Проверить причины отказов', aggregates: [
      { organization_or_region: 'Hospital A', referrals: 30, median_wait_days: null, p90_wait_days: null, refusal_share_pct: 0 },
    ] }, metrics: { waiting: { mae: 2, baseline_mae: 4, model_version: 'test-v3', period: '2025-03-14 - 2025-03-31' } },
  } }
  const html = render(BriefingReview, props)
  assert.match(html, /<td>—<\/td><td>—<\/td><td>0<\/td>/)
  assert.match(html, /test-v3; тест 2025-03-14 - 2025-03-31/)
  assert.match(html, /Актуальные метрики недоступны/)
  assert.match(html, /type="checkbox"/)
  assert.doesNotMatch(html, /checked=""/)
  assert.match(html, /Я проверил период, выбранные стационары, показатели и ограничения/)
  assert.match(render(BriefingReview, { ...props, confirmed: true }), /checked=""/)
})

test('binary requests retain CSRF and surface server context-change errors', async () => {
  const original = globalThis.fetch
  const calls = []
  try {
    globalThis.fetch = async (url, options) => {
      calls.push({ url, options })
      return url.endsWith('/csrf') ? Response.json({ token: 'csrf-test' }) : new Response('%PDF-test', { headers: { 'Content-Type': 'application/pdf' } })
    }
    const result = await api.postPdf('/briefings/pdf', { reviewed: true, review_token: 'test' })
    assert.equal(await result.text(), '%PDF-test')
    assert.equal(calls[1].options.headers['X-CSRF-Token'], 'csrf-test')
    assert.equal(calls[1].options.credentials, 'same-origin')
    globalThis.fetch = async url => url.endsWith('/csrf') ? Response.json({ token: 'csrf-test' }) : Response.json({ detail: 'Контекст изменился' }, { status: 409 })
    await assert.rejects(api.postPdf('/briefings/pdf', {}), error => error.status === 409 && error.message === 'Контекст изменился')
  } finally { globalThis.fetch = original }
})

test('logout invalidates a late PDF response from a previous account', async () => {
  const original = globalThis.fetch
  let release
  let started
  const waiting = new Promise(resolve => { started = resolve })
  try {
    globalThis.fetch = async url => url.endsWith('/csrf') ? Response.json({ token: 'csrf-test' }) : new Promise(resolve => { release = resolve; started() })
    const request = api.postPdf('/briefings/pdf', {})
    await waiting
    api.clearPrivateData()
    release(new Response('%PDF-test'))
    await assert.rejects(request, error => error.name === 'AbortError')
  } finally { globalThis.fetch = original }
})
