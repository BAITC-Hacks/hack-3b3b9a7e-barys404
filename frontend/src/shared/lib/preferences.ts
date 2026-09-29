import { useSyncExternalStore } from 'react'

export type Language = 'ru' | 'kk' | 'en'
export type Theme = 'light' | 'dark'
export type Preferences = Readonly<{ language: Language; theme: Theme }>

export const PREFERENCES_KEY = 'medflow-display-preferences'
const defaults: Preferences = Object.freeze({ language: 'ru', theme: 'light' })
let current: Preferences = defaults
let initialized = false
const listeners = new Set<() => void>()

export function parsePreferences(value: string | null): Preferences {
  try {
    const parsed = JSON.parse(value || '{}')
    return {
      language: ['ru', 'kk', 'en'].includes(parsed?.language) ? parsed.language : 'ru',
      theme: parsed?.theme === 'dark' ? 'dark' : 'light',
    }
  } catch {
    return defaults
  }
}

function applyToDocument() {
  if (typeof document === 'undefined') return
  document.documentElement.lang = current.language
  document.documentElement.dataset.theme = current.theme
  document.documentElement.style.colorScheme = current.theme
  document.title = {
    ru: 'MedFlow AI — аналитика стационаров',
    kk: 'MedFlow AI — стационарлар аналитикасы',
    en: 'MedFlow AI — hospital analytics',
  }[current.language]
  document
    .querySelector('meta[name="theme-color"]')
    ?.setAttribute('content', current.theme === 'dark' ? '#10181e' : '#f6f7f9')
}

function update(next: Preferences, persist: boolean) {
  if (next.language === current.language && next.theme === current.theme) return
  current = Object.freeze(next)
  if (persist && typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(PREFERENCES_KEY, JSON.stringify(current))
    } catch {
      // Preferences still work in memory when browser storage is disabled.
    }
  }
  applyToDocument()
  listeners.forEach((listener) => listener())
}

export function initializePreferences() {
  if (initialized || typeof window === 'undefined') return
  initialized = true
  try {
    current = Object.freeze(parsePreferences(window.localStorage.getItem(PREFERENCES_KEY)))
  } catch {
    current = defaults
  }
  applyToDocument()
  window.addEventListener('storage', (event) => {
    if (event.key === PREFERENCES_KEY || event.key === null) {
      update(parsePreferences(event.newValue), false)
    }
  })
}

export const getPreferences = () => current
export function setLanguage(language: Language) {
  if (['ru', 'kk', 'en'].includes(language)) update({ ...current, language }, true)
}
export function setTheme(theme: Theme) {
  if (theme === 'light' || theme === 'dark') update({ ...current, theme }, true)
}
function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}
export function usePreferences() {
  return useSyncExternalStore(subscribe, getPreferences, getPreferences)
}
