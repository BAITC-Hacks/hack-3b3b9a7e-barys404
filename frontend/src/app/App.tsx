import { Workspace } from './Workspace'
import { AuthGate } from './providers/AuthGate'
import { AccessPendingPage } from '../pages/access-pending/index'
import { AdminPage } from '../pages/admin/index'
import { FrontendVersionNotice } from './providers/FrontendVersionNotice'
import { usePreferences } from '../shared/lib/preferences'

function App() {
  // Re-render translations without remounting pages, forms or the auth session.
  usePreferences()
  return (
    <>
      <FrontendVersionNotice />
      <AuthGate>
        {(user, logout) =>
          user.role === 'platform_admin' ? (
            <AdminPage user={user} logout={logout} />
          ) : user.role === 'hospital_analyst' && !user.hospital_name ? (
            <AccessPendingPage user={user} logout={logout} />
          ) : (
            <Workspace user={user} logout={logout} />
          )
        }
      </AuthGate>
    </>
  )
}

export default App
