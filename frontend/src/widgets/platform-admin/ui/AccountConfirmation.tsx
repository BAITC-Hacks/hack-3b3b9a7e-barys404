import { t } from '../../../shared/lib/i18n'
import { useEffect, useRef } from 'react'
import { type AdminAccount } from '../../../shared/api/types'

export function AccountConfirmation({
  account,
  action,
  busy,
  error,
  cancel,
  confirm,
}: {
  account: AdminAccount
  action: 'access' | 'delete'
  busy: boolean
  error: string
  cancel: () => void
  confirm: () => void
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const node = dialog.current
    node?.showModal()
    return () => node?.close()
  }, [])
  const deleting = action === 'delete'
  const verb = deleting ? t('Удалить') : account.active ? t('Заблокировать') : t('Разблокировать')
  return (
    <dialog
      ref={dialog}
      className="admin-confirmation"
      aria-labelledby="account-confirmation-title"
      onCancel={(event) => {
        event.preventDefault()
        if (!busy) cancel()
      }}
    >
      <span className="section-kicker">{t('УПРАВЛЕНИЕ ДОСТУПОМ')}</span>
      <h2 id="account-confirmation-title">
        {t(
          deleting
            ? 'Удалить аккаунт?'
            : account.active
              ? 'Заблокировать аккаунт?'
              : 'Разблокировать аккаунт?',
        )}
      </h2>
      <strong>{account.display_name}</strong>
      <p className="admin-confirmation-login">{account.login}</p>
      <p>
        {deleting
          ? t(
              'Аккаунт будет удалён без возможности восстановления. Данные больниц и модели останутся без изменений.',
            )
          : account.active
            ? t(
                'Пользователь будет выведен из кабинета и не сможет войти, пока вы не снимете блокировку.',
              )
            : t('Пользователь снова сможет войти с прежним паролем и своей ролью.')}
      </p>
      {error && (
        <p className="admin-warning" role="alert">
          {t(error)}
        </p>
      )}
      <div className="admin-confirmation-actions">
        <button autoFocus className="secondary-button" disabled={busy} onClick={cancel}>
          {t('Отмена')}{' '}
        </button>
        <button
          className={`primary-button ${deleting ? 'admin-delete-confirm' : ''}`}
          disabled={busy}
          onClick={confirm}
        >
          {busy ? t('Сохраняем…') : verb}
        </button>
      </div>
    </dialog>
  )
}
