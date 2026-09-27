export function Pagination({
  total,
  offset,
  size,
  change,
}: {
  total: number
  offset: number
  size: number
  change: (offset: number) => void
}) {
  return (
    <div className="directory-pagination">
      <span>
        {total ? `${offset + 1}–${Math.min(total, offset + size)} из ${total}` : 'Нет записей'}
      </span>
      <div>
        <button disabled={offset === 0} onClick={() => change(Math.max(0, offset - size))}>
          Назад
        </button>
        <button disabled={offset + size >= total} onClick={() => change(offset + size)}>
          Далее
        </button>
      </div>
    </div>
  )
}
