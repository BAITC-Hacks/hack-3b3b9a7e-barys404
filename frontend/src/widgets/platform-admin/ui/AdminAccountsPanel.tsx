import { t } from '../../../shared/lib/i18n'
import { Ban, RefreshCw, ShieldCheck, Trash2, Users } from 'lucide-react'
import { useState } from 'react'
import { post } from '../../../shared/api/client'
import { query } from '../../../entities/hospital/index'
import { type AdminAccount, type AdminAccounts, type User } from '../../../shared/api/types'
import { useRemote } from '../../../shared/lib/useRemote'
import { useSubmittedSearch } from '../../../shared/lib/useSubmittedSearch'
import { number } from '../../../shared/lib/format'
import { roleLabel } from '../../../entities/user/index'
import { EmptyState } from '../../../shared/ui/EmptyState'
import { ErrorState } from '../../../shared/ui/ErrorState'
import { Loading } from '../../../shared/ui/Loading'
import { MetricCard } from '../../../shared/ui/MetricCard'
import { SearchForm } from '../../../shared/ui/SearchForm'
import { AccountConfirmation } from './AccountConfirmation'
import { useStaggeredEntrance } from '../../../shared/lib/useEntrance'

export function AdminAccountsPanel({ user }: { user: User }) {
  const search = useSubmittedSearch()
  const [role, setRole] = useState('')
  const [status, setStatus] = useState('')
  const [offset, setOffset] = useState(0)
  const [revision, setRevision] = useState(0)
  const [confirmation, setConfirmation] = useState<{
    account: AdminAccount
    action: 'access' | 'delete'
  } | null>(null)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState('')
  const [notice, setNotice] = useState<{ key: string; login: string } | null>(null)
  const pageSize = 50
  const { data, loading, error } = useRemote<AdminAccounts>(
    `/admin/users${query({ search: search.applied, role, status, offset, limit: pageSize, refresh: revision })}`,
  )
  const metrics = useStaggeredEntrance<HTMLDivElement>(data?.summary)
  const refresh = () => {
    setOffset(0)
    setRevision((value) => value + 1)
  }
  const chooseAction = (account: AdminAccount, action: 'access' | 'delete') => {
    setActionError('')
    setNotice(null)
    setConfirmation({ account, action })
  }
  const confirm = async () => {
    if (!confirmation || busy) return
    setBusy(true)
    setActionError('')
    const { account, action } = confirmation
    try {
      await post(
        `/admin/users/${encodeURIComponent(account.id)}/${action === 'delete' ? 'delete' : 'status'}`,
        action === 'delete' ? { login: account.login } : { active: !account.active },
      )
      setConfirmation(null)
      setNotice({
        key:
          action === 'delete'
            ? 'Аккаунт {login} удалён.'
            : account.active
              ? 'Аккаунт {login} заблокирован.'
              : 'Аккаунт {login} разблокирован.',
        login: account.login,
      })
      refresh()
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : 'Не удалось выполнить действие.')
    } finally {
      setBusy(false)
    }
  }
  return (
    <>
      {data && (
        <div className="admin-metrics" ref={metrics}>
          <MetricCard
            label={t('Всего аккаунтов')}
            value={number(data.summary.total)}
            icon={Users}
          />
          <MetricCard
            label={t('Доступ открыт')}
            value={number(data.summary.active)}
            icon={ShieldCheck}
          />
          <MetricCard label={t('Заблокированы')} value={number(data.summary.blocked)} icon={Ban} />
        </div>
      )}
      <section className="panel admin-accounts">
        <div className="admin-toolbar">
          <SearchForm
            value={search.draft}
            onChange={search.setDraft}
            onSubmit={() => {
              search.submit()
              setOffset(0)
            }}
            onClear={() => {
              search.clear()
              setOffset(0)
            }}
            placeholder={t('Логин, имя или организация')}
            label={t('Поиск аккаунта')}
          />
          <label>
            {t('Роль')}{' '}
            <select
              value={role}
              onChange={(event) => {
                setRole(event.target.value)
                setOffset(0)
              }}
            >
              <option value="">{t('Все роли')}</option>
              <option value="government_analyst">{t('Аналитик госоргана')}</option>
              <option value="hospital_analyst">{t('Сотрудник больницы')}</option>
              <option value="platform_admin">{t('Администратор')}</option>
            </select>
          </label>
          <label>
            {t('Доступ')}{' '}
            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value)
                setOffset(0)
              }}
            >
              <option value="">{t('Все аккаунты')}</option>
              <option value="active">{t('Открыт')}</option>
              <option value="blocked">{t('Заблокирован')}</option>
            </select>
          </label>
          <button
            className="secondary-button"
            onClick={refresh}
            disabled={loading || busy}
            aria-label={t('Обновить аккаунты')}
          >
            <RefreshCw size={17} /> {t('Обновить')}{' '}
          </button>
        </div>
        {notice && (
          <p className="admin-notice" role="status">
            {t(notice.key, { login: notice.login })}
          </p>
        )}
        {loading && <Loading />}
        {error && <ErrorState message={t(error)} />}
        {data &&
          (data.items.length ? (
            <>
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <caption className="admin-sr-only">{t('Аккаунты сотрудников')}</caption>
                  <thead>
                    <tr>
                      <th>{t('Аккаунт')}</th>
                      <th>{t('Роль')}</th>
                      <th>{t('Организация')}</th>
                      <th>{t('Доступ')}</th>
                      <th>{t('Действия')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.items.map((account) => {
                      const self = account.id === user.id
                      return (
                        <tr key={account.id}>
                          <td data-label={t('Аккаунт')}>
                            <strong>{account.display_name}</strong>
                            <small>
                              {account.login}
                              {self ? t(' · Ваш аккаунт') : ''}
                            </small>
                          </td>
                          <td data-label={t('Роль')}>{roleLabel(account.role)}</td>
                          <td data-label={t('Организация')} className="admin-organization">
                            {account.role === 'government_analyst'
                              ? t('Все больницы')
                              : account.role === 'platform_admin'
                                ? t('Управление платформой')
                                : account.hospital_name || t('Организация не назначена')}
                            {account.role === 'hospital_analyst' &&
                              !account.organization_active && (
                                <small className="admin-warning">
                                  {t('Организация недоступна')}
                                </small>
                              )}
                          </td>
                          <td data-label={t('Доступ')}>
                            <span
                              className={`admin-status ${account.active ? 'is-active' : 'is-blocked'}`}
                            >
                              {account.active ? t('Открыт') : t('Заблокирован')}
                            </span>
                          </td>
                          <td data-label={t('Действия')}>
                            <div className="admin-row-actions">
                              <button
                                className="admin-action"
                                disabled={self || busy}
                                title={self ? t('Нельзя заблокировать свой аккаунт') : undefined}
                                aria-label={t(
                                  account.active
                                    ? 'Заблокировать {login}'
                                    : 'Разблокировать {login}',
                                  { login: account.login },
                                )}
                                onClick={() => chooseAction(account, 'access')}
                              >
                                {account.active ? <Ban size={16} /> : <ShieldCheck size={16} />}{' '}
                                {account.active ? t('Блокировать') : t('Разблокировать')}
                              </button>
                              <button
                                className="admin-action admin-danger"
                                disabled={self || busy}
                                title={self ? t('Нельзя удалить свой аккаунт') : undefined}
                                aria-label={t('Удалить {login}', { login: account.login })}
                                onClick={() => chooseAction(account, 'delete')}
                              >
                                <Trash2 size={16} /> {t('Удалить')}{' '}
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              <div className="directory-pagination">
                <span>
                  {t('{start}–{end} из {total}', {
                    start: number(offset + 1),
                    end: number(offset + data.items.length),
                    total: number(data.total),
                  })}
                </span>
                <div>
                  <button
                    disabled={offset === 0 || busy}
                    onClick={() => setOffset(Math.max(0, offset - pageSize))}
                  >
                    {t('Назад')}{' '}
                  </button>
                  <button
                    disabled={offset + pageSize >= data.total || busy}
                    onClick={() => setOffset(offset + pageSize)}
                  >
                    {t('Далее')}{' '}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <EmptyState
              title={t('Аккаунты не найдены')}
              text={t('Измените поиск, роль или статус доступа.')}
            />
          ))}
      </section>
      {confirmation && (
        <AccountConfirmation
          account={confirmation.account}
          action={confirmation.action}
          busy={busy}
          error={actionError}
          cancel={() => {
            if (!busy) setConfirmation(null)
          }}
          confirm={() => void confirm()}
        />
      )}
    </>
  )
}
