export function StatusPill({ good, children }: { good: boolean; children: React.ReactNode }) {
  return (
    <span className={`status-pill ${good ? 'status-good' : 'status-muted'}`}>
      <span className="status-dot" />
      {children}
    </span>
  )
}
