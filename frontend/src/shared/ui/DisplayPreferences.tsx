import { Moon, Sun } from 'lucide-react'
import { t } from '../lib/i18n'
import { setLanguage, setTheme, usePreferences } from '../lib/preferences'

export function DisplayPreferences() {
  const { language, theme } = usePreferences()
  const nextTheme = theme === 'dark' ? 'light' : 'dark'
  const themeLabel = theme === 'dark' ? t('Включить светлую тему') : t('Включить тёмную тему')

  return (
    <div className="display-preferences" role="group" aria-label={t('Язык и оформление')}>
      <select
        className="language-select"
        aria-label={t('Язык интерфейса')}
        value={language}
        onChange={(event) => setLanguage(event.target.value as 'ru' | 'kk' | 'en')}
      >
        <option value="ru" lang="ru">
          Русский
        </option>
        <option value="kk" lang="kk">
          Қазақша
        </option>
        <option value="en" lang="en">
          English
        </option>
      </select>
      <button
        type="button"
        className="icon-button theme-toggle"
        onClick={() => setTheme(nextTheme)}
        aria-label={themeLabel}
        title={themeLabel}
      >
        {theme === 'dark' ? (
          <Sun size={19} aria-hidden="true" />
        ) : (
          <Moon size={19} aria-hidden="true" />
        )}
      </button>
    </div>
  )
}
