import { LockKeyhole } from 'lucide-react'
import { useState } from 'react'
import { post } from '../api/client'

export function ChangePasswordPage({
  onDone,
  onLogout,
}: {
  onDone: () => void
  onLogout: () => Promise<void>
}) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  return (
    <main className="auth-state">
      <div className="login-form-card">
        <LockKeyhole size={25} />
        <h1>Установите свой пароль</h1>
        <p>
          Вы вошли с временным паролем. Перед началом работы замените его на личный — от 12 до 128
          символов.
        </p>
        <form
          onSubmit={async (event) => {
            event.preventDefault()
            setBusy(true)
            setError('')
            try {
              await post('/auth/change-password', { current_password: current, new_password: next })
              onDone()
            } catch (reason) {
              setError(reason instanceof Error ? reason.message : 'Ошибка')
            } finally {
              setBusy(false)
            }
          }}
        >
          <label>
            Временный пароль
            <input
              type="password"
              autoComplete="current-password"
              value={current}
              onChange={(e) => setCurrent(e.target.value)}
              required
            />
          </label>
          <label>
            Новый пароль
            <input
              type="password"
              autoComplete="new-password"
              minLength={12}
              maxLength={128}
              value={next}
              onChange={(e) => setNext(e.target.value)}
              required
            />
          </label>
          {error && (
            <p className="message message-error" role="alert">
              {error}
            </p>
          )}
          <button className="primary-button" disabled={busy}>
            Сохранить пароль
          </button>
        </form>
        <button
          className="text-button"
          onClick={() => {
            void onLogout().catch((reason) => setError(reason.message))
          }}
        >
          Выйти
        </button>
      </div>
    </main>
  )
}
