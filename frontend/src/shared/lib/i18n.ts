import { guideMessages } from './messages/guide'
import { getPreferences } from './preferences'
import { commonMessages } from './messages/common'
import { errorMessages } from './messages/errors'
import { analyticsMessages } from './messages/analytics'
import { accessMessages } from './messages/access'
import { themeMessages } from './messages/theme'
import { serverAliases } from './messages/serverAliases'

export const messages: Record<string, { kk: string; en: string }> = {
  ...commonMessages,
  ...errorMessages,
  ...analyticsMessages,
  ...accessMessages,
  ...themeMessages,
  ...guideMessages,
}

export const getLocale = () =>
  ({ ru: 'ru-RU', kk: 'kk-KZ', en: 'en-GB' })[getPreferences().language]

// Source text is the Russian catalogue and a safe fallback for data-owned labels.
// Call at render time, not while constructing module-level constants.
export function t(source: string, params: Record<string, string | number> = {}): string {
  if (Object.hasOwn(serverAliases, source)) source = serverAliases[source]
  const language = getPreferences().language
  const translated =
    language === 'ru' || !Object.hasOwn(messages, source) ? source : messages[source][language]
  return translated.replace(/\{(\w+)\}/g, (match, key: string) =>
    Object.hasOwn(params, key) ? String(params[key]) : match,
  )
}
