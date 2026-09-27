import { type User } from '../api/types'
import { UserMenu } from '../components/layout/UserMenu'
import { PageHeading } from '../components/ui/PageHeading'
import { DataPage } from './DataPage'

export function AdminPage({ user, logout }: { user: User; logout: () => Promise<void> }) {
  return (
    <div className="admin-shell">
      <header className="topbar">
        <strong>MedFlow AI · Администрирование</strong>
        <UserMenu user={user} logout={logout} />
      </header>
      <main className="content">
        <PageHeading
          eyebrow="АДМИНИСТРАТОР"
          title="Управление доступом"
          description="Учётные записи управляются локальным оператором. Аналитика доступна в отдельных кабинетах сотрудников."
        />
        <section className="panel">
          <h2>Команды оператора</h2>
          <p>
            Список пользователей: <code>python -m scripts.auth users</code>
          </p>
          <p>
            Выдача и отзыв доступа: <code>python -m scripts.auth --help</code>
          </p>
        </section>
        <DataPage />
      </main>
    </div>
  )
}
