import { ErrorBox } from './ErrorBox'

export function Pending({ error }: { error: string }) {
  return error ? (
    <ErrorBox text={error} />
  ) : (
    <div className="loading-state" role="status">
      Загружаем данные…
    </div>
  )
}
