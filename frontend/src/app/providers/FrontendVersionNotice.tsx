import { t } from '../../shared/lib/i18n'
import { useEffect, useState } from 'react'
import { get } from '../../shared/api/client'

// A hash-route change does not reload JavaScript already running in a SPA tab.
export function FrontendVersionNotice() {
  const [outdated, setOutdated] = useState(false)
  useEffect(() => {
    const loadedAssets = Array.from(document.querySelectorAll('script[src], link[href]'))
      .map((element) => element.getAttribute('src') || element.getAttribute('href') || '')
      .filter((path) => /^\/assets\/.*\.(js|css)$/.test(path))
      .sort()
    if (!loadedAssets.length) return // Vite development uses HMR.
    const controller = new AbortController()
    let lastCheck = 0
    let pending = false
    const check = async () => {
      if (document.hidden || pending || Date.now() - lastCheck < 10000) return
      lastCheck = Date.now()
      pending = true
      try {
        const version = await get<{ assets: string[] }>('/frontend-version', controller.signal)
        if (
          !controller.signal.aborted &&
          version.assets.length &&
          JSON.stringify(version.assets) !== JSON.stringify(loadedAssets)
        )
          setOutdated(true)
      } catch {
        // Offline or rebuilding: do not interrupt the current form; retry later.
      } finally {
        pending = false
      }
    }
    void check()
    const timer = window.setInterval(check, 60000)
    window.addEventListener('focus', check)
    window.addEventListener('hashchange', check)
    document.addEventListener('visibilitychange', check)
    return () => {
      controller.abort()
      window.clearInterval(timer)
      window.removeEventListener('focus', check)
      window.removeEventListener('hashchange', check)
      document.removeEventListener('visibilitychange', check)
    }
  }, [])
  if (!outdated) return null
  return (
    <aside className="frontend-version-notice" aria-label={t('Обновление интерфейса')}>
      <span role="status">
        {t('Доступна новая версия интерфейса. Завершите ввод перед обновлением.')}
      </span>
      <button
        className="secondary-button"
        title={t('Обновление сбросит выбранные параметры страницы')}
        onClick={() => window.location.reload()}
      >
        {t('Обновить страницу')}{' '}
      </button>
    </aside>
  )
}
