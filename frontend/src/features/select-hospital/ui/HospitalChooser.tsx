import { Building2, Check, ChevronDown, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useEntrance } from '../../../shared/lib/useEntrance'
import { hospitalDisplayName } from '../../../entities/hospital/index'

export function HospitalChooser({
  hospital,
  hospitals,
  choose,
}: {
  hospital: string
  hospitals: string[]
  choose: (hospital: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const entrance = useEntrance<HTMLDivElement>()
  const matches = useMemo(() => {
    const term = search.trim().toLocaleLowerCase('ru-RU')
    return term
      ? hospitals.filter((name) => name.toLocaleLowerCase('ru-RU').includes(term)).slice(0, 50)
      : [hospital, ...hospitals.filter((name) => name !== hospital).slice(0, 7)]
  }, [search, hospitals, hospital])
  return (
    <div className="hospital-chooser">
      <button
        className="chooser-trigger"
        onClick={() => {
          setOpen(!open)
          setSearch('')
        }}
        aria-expanded={open}
        aria-label="Выбрать стационар"
        title={hospital}
      >
        <Building2 size={16} />
        <span>{hospitalDisplayName(hospital)}</span>
        <ChevronDown size={15} />
      </button>
      {open && (
        <div className="chooser-popover" ref={entrance}>
          <div className="chooser-search">
            <Search size={15} />
            <input
              autoFocus
              placeholder="Найти стационар"
              aria-label="Найти стационар"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Escape') setOpen(false)
                if (event.key === 'Enter' && matches[0]) {
                  choose(matches[0])
                  setOpen(false)
                }
              }}
            />
          </div>
          <div className="chooser-list">
            {matches.length ? (
              matches.map((name) => (
                <button
                  key={name}
                  title={name}
                  onClick={() => {
                    choose(name)
                    setOpen(false)
                  }}
                >
                  <span>{hospitalDisplayName(name)}</span>
                  {name === hospital && <Check size={14} />}
                </button>
              ))
            ) : (
              <p>Ничего не найдено</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
