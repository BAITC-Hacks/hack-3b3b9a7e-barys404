import assert from 'node:assert/strict'
import test from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { load } from './helpers/load.mjs'

const ui = await load('tests/helpers/localization.ts')
const render = (component, props = {}) => renderToStaticMarkup(createElement(component, props))

test('saved preferences restore safely, update document metadata and follow another tab', () => {
  const previousWindow = globalThis.window
  const previousDocument = globalThis.document
  const values = new Map([[ui.PREFERENCES_KEY, '{"language":"kk","theme":"dark"}']])
  const handlers = new Map()
  const meta = {}
  try {
    globalThis.window = {
      localStorage: {
        getItem: (key) => values.get(key) ?? null,
        setItem: (key, value) => values.set(key, value),
      },
      addEventListener: (name, handler) => handlers.set(name, handler),
    }
    globalThis.document = {
      documentElement: { dataset: {}, style: {} },
      querySelector: () => ({
        setAttribute: (key, value) => {
          meta[key] = value
        },
      }),
    }
    ui.initializePreferences()
    assert.deepEqual(ui.getPreferences(), { language: 'kk', theme: 'dark' })
    assert.equal(document.documentElement.lang, 'kk')
    assert.equal(document.documentElement.dataset.theme, 'dark')
    assert.equal(document.documentElement.style.colorScheme, 'dark')
    assert.match(document.title, /стационарлар/)
    ui.setLanguage('en')
    assert.deepEqual(JSON.parse(values.get(ui.PREFERENCES_KEY)), { language: 'en', theme: 'dark' })
    ui.setTheme('light')
    assert.equal(document.documentElement.dataset.theme, 'light')
    assert.equal(document.documentElement.lang, 'en')
    assert.match(document.title, /hospital analytics/)
    handlers.get('storage')({
      key: ui.PREFERENCES_KEY,
      newValue: '{"language":"ru","theme":"dark"}',
    })
    assert.deepEqual(ui.getPreferences(), { language: 'ru', theme: 'dark' })
    assert.equal(document.documentElement.lang, 'ru')
    handlers.get('storage')({ key: null, newValue: null })
    assert.deepEqual(ui.getPreferences(), { language: 'ru', theme: 'light' })
    window.localStorage.setItem = () => {
      throw new Error('Storage disabled')
    }
    assert.doesNotThrow(() => ui.setLanguage('en'))
    assert.equal(ui.getPreferences().language, 'en')
  } finally {
    globalThis.window = previousWindow
    globalThis.document = previousDocument
    ui.setLanguage('ru')
    ui.setTheme('light')
  }
})

test('invalid settings fall back safely and arbitrary values cannot enter the store', () => {
  for (const raw of [null, '{', 'null', '42', '{"language":"xx","theme":"sepia"}']) {
    assert.deepEqual(ui.parsePreferences(raw), { language: 'ru', theme: 'light' })
  }
  ui.setLanguage('unknown')
  ui.setTheme('unknown')
  assert.deepEqual(ui.getPreferences(), { language: 'ru', theme: 'light' })
})

test('all catalogue translations preserve placeholders and untranslated source data', () => {
  const placeholders = (text) => [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort()
  for (const [source, translations] of Object.entries(ui.messages)) {
    for (const language of ['kk', 'en']) {
      assert.ok(translations[language].trim(), `${language}: ${source}`)
      assert.deepEqual(
        placeholders(translations[language]),
        placeholders(source),
        `${language}: ${source}`,
      )
    }
  }
  try {
    ui.setLanguage('en')
    assert.equal(ui.t('{count} направл.', { count: 24 }), '24 referrals')
    assert.equal(ui.t('Городская больница №2'), 'Городская больница №2')
    assert.equal(ui.t('toString'), 'toString')
    assert.equal(ui.t('неизвестное значение {x}', { x: '$&' }), 'неизвестное значение $&')
  } finally {
    ui.setLanguage('ru')
  }
})

test('language changes affect numbers, dates and region labels without changing region codes', () => {
  try {
    ui.setLanguage('ru')
    assert.equal(ui.decimal(5.27, 2), '5,27')
    assert.equal(ui.organizations(21), '21 организация')
    ui.setLanguage('en')
    assert.equal(ui.decimal(5.27, 2), '5.27')
    assert.equal(ui.organizations(21), '21 organisations')
    assert.equal(ui.organizations(1), '1 organisation')
    assert.match(ui.day('2025-03-31'), /Mar/)
    assert.equal(ui.regionLabel('31'), 'Zhambyl Region · 31')
    ui.setLanguage('kk')
    assert.equal(ui.regionLabel('31'), 'Жамбыл облысы · 31')
    assert.equal(ui.regionLabel('99'), 'Өңір · 99')
    assert.equal(ui.organizations(21), '21 ұйым')
    assert.equal(ui.REGION_NAMES['31'], 'Жамбылская область')
  } finally {
    ui.setLanguage('ru')
  }
})

test('login, navigation, controls and existing server errors render in all three languages', () => {
  const expectations = {
    ru: { login: 'Вход в кабинет', nav: 'Обзор', error: 'Неверный логин или пароль.' },
    kk: { login: 'Кабинетке кіру', nav: 'Шолу', error: 'Логин немесе құпиясөз қате.' },
    en: { login: 'Sign in', nav: 'Overview', error: 'Incorrect username or password.' },
  }
  try {
    for (const [language, expected] of Object.entries(expectations)) {
      ui.setLanguage(language)
      const login = render(ui.LoginPage, { onLogin: () => {}, notice: '' })
      assert.ok(login.includes(expected.login), language)
      assert.match(login, /type="password"/)
      assert.match(login, new RegExp(`value="${language}"[^>]*selected=""`), language)
      const nav = render(ui.Sidebar, {
        items: ui.NAV,
        activeView: 'overview',
        mode: 'government',
        navigate: () => {},
        onHospital: () => {},
      })
      assert.ok(nav.includes(expected.nav), language)
      assert.match(nav, /aria-current="page"/)
      assert.ok(
        render(ui.ErrorBox, { text: 'Неверный логин или пароль.' }).includes(expected.error),
      )
      ui.setTheme('dark')
      assert.ok(render(ui.DisplayPreferences).includes(ui.t('Включить светлую тему')))
      ui.setTheme('light')
      assert.ok(render(ui.DisplayPreferences).includes(ui.t('Включить тёмную тему')))
    }
  } finally {
    ui.setLanguage('ru')
    ui.setTheme('light')
  }
})

test('translated forecast keeps the estimate and translated filters keep API values', () => {
  const result = {
    prediction: 2.5,
    clipped: false,
    method: 'hospital_profile_median',
    support: 125,
    mae: 5.27,
  }
  const filters = {
    start: '2025-01-01',
    end: '2025-03-31',
    region: '31',
    profile: 'Неврологический',
  }
  const bootstrap = {
    period: { start: filters.start, end: filters.end },
    regions: ['31', '75'],
    profiles: ['Неврологический'],
  }
  try {
    ui.setLanguage('en')
    const card = render(ui.WaitEstimateCard, { result })
    assert.match(card, /aria-label="2 d 12 h"/)
    assert.match(card, /5\.27/)
    assert.equal(result.prediction, 2.5)
    const props = {
      filters,
      bootstrap,
      setFilters: () => {
        throw new Error('Rendering must not apply filters')
      },
    }
    const html = render(ui.FilterBar, props)
    assert.match(html, /value="31" selected="">Zhambyl Region · 31/)
    assert.match(html, /value="Неврологический"/)
    assert.match(html, /Referral filters/)
    assert.match(html, /type="submit" disabled="">Apply/)
    assert.deepEqual(filters, {
      start: '2025-01-01',
      end: '2025-03-31',
      region: '31',
      profile: 'Неврологический',
    })
    ui.setLanguage('kk')
    assert.match(render(ui.WaitEstimateCard, { result }), /aria-label="2 күн 12 сағ"/)
    ui.setLanguage('ru')
    assert.match(render(ui.WaitEstimateCard, { result }), /aria-label="2 д 12 ч"/)
    assert.equal(
      ui.t('Failed to fetch'),
      'Не удалось подключиться к серверу. Проверьте соединение.',
    )
  } finally {
    ui.setLanguage('ru')
  }
})
