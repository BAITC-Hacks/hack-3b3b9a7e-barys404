import { DisplayPreferences } from '../../../shared/ui/DisplayPreferences'
import { t } from '../../../shared/lib/i18n'
import { ArrowRight, ChevronLeft, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { post } from '../../../shared/api/client'
import { type User } from '../../../shared/api/types'
import { Brand } from '../../../shared/ui/Brand'
import { useEntrance } from '../../../shared/lib/useEntrance'

export function LoginPage({ onLogin, notice }: { onLogin: (user: User) => void; notice: string }) {
  const entrance = useEntrance<HTMLDivElement>()
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      onLogin(await post<User>('/auth/login', { login: login.trim(), password }))
    } catch (reason) {
      if (!(reason instanceof DOMException && reason.name === 'AbortError'))
        setError(reason instanceof Error ? reason.message : 'Не удалось войти.')
    } finally {
      setBusy(false)
    }
  }
  return (
    <div className="login-page">
      <div className="login-story">
        <Brand />
        <div>
          <h2>{t('Рабочий кабинет')}</h2>
          <p>{t('Платформа откроет разделы, доступные вашей учётной записи.')}</p>
          <dl className="login-scopes">
            <div>
              <dt>{t('Больница')}</dt>
              <dd>{t('Направления и прогнозы своей организации')}</dd>
            </div>
            <div>
              <dt>{t('Госорган')}</dt>
              <dd>{t('Общий обзор и сравнение стационаров')}</dd>
            </div>
            <div>
              <dt>{t('Администратор')}</dt>
              <dd>{t('Аккаунты сотрудников и состояние системы')}</dd>
            </div>
          </dl>
        </div>
        <span className="login-security">
          <ShieldCheck size={19} /> {t('Доступ к данным ограничен ролью и организацией')}{' '}
        </span>
      </div>
      <main className="login-main">
        <div className="login-preferences">
          <DisplayPreferences />
        </div>
        <a className="back-link" href="#welcome">
          <ChevronLeft size={16} /> {t('О платформе')}{' '}
        </a>
        <div className="login-form-card" ref={entrance}>
          <h1>{t('Вход в кабинет')}</h1>
          <p>{t('Используйте учётную запись, выданную администратором.')}</p>
          {notice && (
            <div className="auth-notice" role="status">
              {t(notice)}
            </div>
          )}
          <form onSubmit={submit}>
            <label>
              {t('Логин')}{' '}
              <input
                autoComplete="username"
                required
                maxLength={120}
                value={login}
                onChange={(event) => setLogin(event.target.value)}
                placeholder={t('Ваш логин')}
              />
            </label>
            <label>
              {t('Пароль')}{' '}
              <span className="password-input">
                <input
                  type={show ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  maxLength={128}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder={t('Введите пароль')}
                />
                <button
                  type="button"
                  onClick={() => setShow(!show)}
                  aria-label={show ? t('Скрыть пароль') : t('Показать пароль')}
                  aria-pressed={show}
                >
                  {show ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
            </label>
            {error && (
              <div className="message message-error" role="alert">
                {t(error)}
              </div>
            )}
            <button className="primary-button" disabled={busy}>
              {busy ? t('Входим…') : t('Войти в кабинет')}
              <ArrowRight size={17} />
            </button>
          </form>
          <div className="login-help">
            <strong>{t('Нет доступа или забыли пароль?')}</strong>
            <p>
              {t('Обратитесь к администратору платформы для получения или восстановления доступа.')}
            </p>
          </div>
        </div>
        <small className="login-caption">
          {t('MedFlow AI · Аналитика на исторических данных')}
        </small>
      </main>
    </div>
  )
}
