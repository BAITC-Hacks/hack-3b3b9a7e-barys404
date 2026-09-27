import { Workspace } from './app/Workspace'
import { AuthGate } from './auth/AuthGate'
import { AccessPendingPage } from './pages/AccessPendingPage'
import { AdminPage } from './pages/AdminPage'

function App() {
  return (
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
  )
}

export default App
