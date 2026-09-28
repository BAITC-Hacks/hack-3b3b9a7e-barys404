import { Search, X } from 'lucide-react'

export function SearchForm({
  value,
  onChange,
  onSubmit,
  onClear,
  label,
  placeholder,
  className = '',
}: {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  onClear: () => void
  label: string
  placeholder: string
  className?: string
}) {
  return (
    <form
      role="search"
      aria-label={label}
      className={`search-field ${className}`.trim()}
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit()
      }}
    >
      <input
        type="text"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        aria-label={label}
      />
      {value && (
        <button type="button" onClick={onClear} aria-label="Очистить поиск">
          <X size={16} />
        </button>
      )}
      <button type="submit" className="search-submit" aria-label="Найти" title="Найти">
        <Search size={19} aria-hidden="true" />
      </button>
    </form>
  )
}
