import { Search, X } from 'lucide-react'
import { t } from '../lib/i18n'

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
      aria-label={t(label)}
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
        placeholder={t(placeholder)}
        aria-label={t(label)}
      />
      {value && (
        <button type="button" onClick={onClear} aria-label={t('Очистить поиск')}>
          <X size={16} />
        </button>
      )}
      <button type="submit" className="search-submit" aria-label={t('Найти')} title={t('Найти')}>
        <Search size={19} aria-hidden="true" />
      </button>
    </form>
  )
}
