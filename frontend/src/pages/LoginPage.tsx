import { ArrowRight, ChevronLeft, Eye, EyeOff, LockKeyhole, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { post } from '../api/client'
import { type User } from '../api/types'
import { Brand } from '../components/layout/Brand'

export function LoginPage({ onLogin, notice }: { onLogin: (user: User) => void; notice: string }) {
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
          <span className="public-eyebrow">ВАШЕ РАБОЧЕЕ ПРОСТРАНСТВО</span>
          <h1>
            Данные вашей организации.
            <br />
            Ваши решения.
          </h1>
          <p>
            Войдите, чтобы открыть аналитику и прогнозы. Платформа автоматически загрузит кабинет с
            правами вашей учётной записи.
          </p>
        </div>
        <span className="login-security">
          <ShieldCheck size={19} /> Доступ к данным ограничен ролью и организацией
        </span>
      </div>
      <main className="login-main">
        <a className="back-link" href="#welcome">
          <ChevronLeft size={16} /> О платформе
        </a>
        <div className="login-form-card">
          <span className="login-lock">
            <LockKeyhole size={23} />
          </span>
          <h2>Вход в кабинет</h2>
          <p>Используйте учётную запись, выданную администратором.</p>
          {notice && (
            <div className="auth-notice" role="status">
              {notice}
            </div>
          )}
          <form onSubmit={submit}>
            <label>
              Логин
              <input
                autoComplete="username"
                autoFocus
                required
                maxLength={120}
                value={login}
                onChange={(event) => setLogin(event.target.value)}
                placeholder="Ваш логин"
              />
            </label>
            <label>
              Пароль
              <span className="password-input">
                <input
                  type={show ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  maxLength={128}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Введите пароль"
                />
                <button
                  type="button"
                  onClick={() => setShow(!show)}
                  aria-label={show ? 'Скрыть пароль' : 'Показать пароль'}
                >
                  {show ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
            </label>
            {error && (
              <div className="message message-error" role="alert">
                {error}
              </div>
            )}
            <button className="primary-button" disabled={busy}>
              {busy ? 'Входим…' : 'Войти в кабинет'}
              <ArrowRight size={17} />
            </button>
          </form>
          <div className="login-help">
            <strong>Нет доступа или забыли пароль?</strong>
            <p>
              Обратитесь к администратору платформы. Он создаст учётную запись или поможет
              восстановить доступ.
            </p>
          </div>
        </div>
        <small className="login-caption">MedFlow AI · Аналитика на исторических данных</small>
      </main>
    </div>
  )
}
