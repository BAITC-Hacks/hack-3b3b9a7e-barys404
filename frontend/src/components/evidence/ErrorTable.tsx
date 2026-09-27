import { type ErrorMetrics } from '../../api/types'
import { day, metric } from '../../lib/evidenceFormat'

export function ErrorTable({
  rows,
}: {
  rows: (ErrorMetrics & {
    test_start: string
    test_end: string
  })[]
}) {
  return (
    <div className="evidence-table-wrap">
      <table className="evidence-table">
        <thead>
          <tr>
            <th>Период регистрации теста</th>
            <th>MAE</th>
            <th>Baseline MAE</th>
            <th>RMSE</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.test_start}>
              <th>
                {day(row.test_start)} — {day(row.test_end)}
              </th>
              <td>{metric(row.mae)}</td>
              <td>{metric(row.baseline_mae)}</td>
              <td>{metric(row.rmse)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
