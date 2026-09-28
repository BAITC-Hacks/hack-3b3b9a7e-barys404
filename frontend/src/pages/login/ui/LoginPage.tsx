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
          <h2>Рабочий кабинет</h2>
          <p>Платформа откроет разделы, доступные вашей учётной записи.</p>
          <dl className="login-scopes">
            <div>
              <dt>Больница</dt>
              <dd>Направления и прогнозы своей организации</dd>
            </div>
            <div>
              <dt>Госорган</dt>
              <dd>Общий обзор и сравнение стационаров</dd>
            </div>
            <div>
              <dt>Администратор</dt>
              <dd>Аккаунты сотрудников и состояние системы</dd>
            </div>
          </dl>
        </div>
        <span className="login-security">
          <ShieldCheck size={19} /> Доступ к данным ограничен ролью и организацией
        </span>
      </div>
      <main className="login-main">
        <a className="back-link" href="#welcome">
          <ChevronLeft size={16} /> О платформе
        </a>
        <div className="login-form-card" ref={entrance}>
          <h1>Вход в кабинет</h1>
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
                  aria-pressed={show}
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
            <p>Обратитесь к администратору платформы для получения или восстановления доступа.</p>
          </div>
        </div>
        <small className="login-caption">MedFlow AI · Аналитика на исторических данных</small>
      </main>
    </div>
  )
}
