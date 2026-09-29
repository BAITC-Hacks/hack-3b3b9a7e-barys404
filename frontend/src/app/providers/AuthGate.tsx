import { t } from '../../shared/lib/i18n'
import { type ReactNode, useEffect, useRef, useState } from 'react'
import { ApiError, clearPrivateData, get, post } from '../../shared/api/client'
import { type User } from '../../shared/api/types'
import { ChangePasswordPage } from '../../pages/change-password/index'
import { LoginPage } from '../../pages/login/index'
import { WelcomePage } from '../../pages/welcome/index'

export function AuthGate({
  children,
}: {
  children: (user: User, logout: () => Promise<void>) => ReactNode
}) {
  const [user, setUser] = useState<User | null>(null)
  const [checking, setChecking] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [hash, setHash] = useState(window.location.hash)
  const channel = useRef<BroadcastChannel | null>(null)
  const version = useRef(0)
  const reset = (message: string) => {
    version.current++
    clearPrivateData()
    setUser(null)
    setChecking(false)
    setError('')
    setNotice(message)
  }
  const check = async () => {
    const attempt = ++version.current
    try {
      const account = await get<User>('/auth/me')
      if (attempt === version.current) {
        setUser(account)
        setError('')
      }
    } catch (reason) {
      if (
        attempt !== version.current ||
        (reason instanceof DOMException && reason.name === 'AbortError')
      )
        return
      if (reason instanceof ApiError && reason.status === 401) reset('')
      else setError('Не удалось связаться с сервером. Проверьте подключение и повторите попытку.')
    } finally {
      if (attempt === version.current) setChecking(false)
    }
  }
  useEffect(() => {
    void check()
    const route = () => setHash(window.location.hash)
    const expired = () => {
      reset('Сессия завершена. Войдите снова, чтобы продолжить.')
      window.location.hash = 'login'
    }
    const tab = new BroadcastChannel('medflow-session')
    channel.current = tab
    tab.onmessage = () => {
      reset('Учётная запись изменена в другой вкладке.')
      setChecking(true)
      void check()
    }
    const restored = (event: PageTransitionEvent) => {
      if (event.persisted) {
        reset('')
        setChecking(true)
        void check()
      }
    }
    window.addEventListener('hashchange', route)
    window.addEventListener('session-expired', expired)
    window.addEventListener('pageshow', restored)
    return () => {
      version.current++
      clearPrivateData()
      tab.close()
      window.removeEventListener('hashchange', route)
      window.removeEventListener('session-expired', expired)
      window.removeEventListener('pageshow', restored)
    }
  }, [])
  useEffect(() => {
    if (!user) return
    let lastActivity = Date.now()
    const activity = () => {
      if (Date.now() - lastActivity < 60000) return
      lastActivity = Date.now()
      void post('/auth/activity', {}).catch(() => {})
    }
    const verify = async () => {
      try {
        const latest = await get<User>('/auth/me')
        if (
          latest.id !== user.id ||
          latest.role !== user.role ||
          latest.hospital_id !== user.hospital_id
        ) {
          reset('')
          setChecking(true)
          void check()
        }
      } catch (reason) {
        if (reason instanceof ApiError && reason.status === 401) {
          reset('Сессия завершена. Войдите снова.')
          window.location.hash = 'login'
        }
      }
    }
    const interval = window.setInterval(verify, 60000)
    const focus = () => {
      void verify()
    }
    window.addEventListener('pointerdown', activity)
    window.addEventListener('keydown', activity)
    window.addEventListener('focus', focus)
    return () => {
      window.clearInterval(interval)
      window.removeEventListener('pointerdown', activity)
      window.removeEventListener('keydown', activity)
      window.removeEventListener('focus', focus)
    }
  }, [user])
  const logout = async () => {
    await post('/auth/logout', {})
    reset('Вы вышли из аккаунта.')
    channel.current?.postMessage('changed')
    window.location.hash = 'login'
  }
  if (checking)
    return (
      <main className="auth-state">
        <div className="spinner" />
        <p>{t('Проверяем сеанс…')}</p>
      </main>
    )
  if (error && !user)
    return (
      <main className="auth-state">
        <p role="alert">{t(error)}</p>
        <button
          className="primary-button"
          onClick={() => {
            setChecking(true)
            void check()
          }}
        >
          {t('Повторить')}{' '}
        </button>
      </main>
    )
  if (user?.must_change_password)
    return (
      <ChangePasswordPage
        onLogout={logout}
        onDone={() => {
          reset('Пароль изменён. Войдите с новым паролем.')
          channel.current?.postMessage('changed')
          window.location.hash = 'login'
        }}
      />
    )
  if (user) return <div key={user.id}>{children(user, logout)}</div>
  const showLogin = hash && hash !== '#welcome'
  return showLogin ? (
    <LoginPage
      notice={t(notice)}
      onLogin={(account) => {
        clearPrivateData()
        setUser(account)
        setNotice('')
        channel.current?.postMessage('changed')
        if (['#login', '#welcome', ''].includes(window.location.hash))
          window.location.hash = 'overview'
      }}
    />
  ) : (
    <WelcomePage />
  )
}
