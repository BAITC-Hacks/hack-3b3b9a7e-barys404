export function Loading({ label = 'Загружаем данные' }: { label?: string }) {
  return (
    <div className="loading-state">
      <div className="spinner" />
      <span>{label}…</span>
    </div>
  )
}
