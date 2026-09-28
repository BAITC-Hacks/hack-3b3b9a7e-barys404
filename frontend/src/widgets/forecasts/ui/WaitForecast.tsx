import { ArrowRight, Clock3 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { post } from '../../../shared/api/client'
import { query, hospitalId } from '../../../entities/hospital/index'
import { type WaitOptions, type WaitResult } from '../../../shared/api/types'
import { useRemote } from '../../../shared/lib/useRemote'
import { day, decimal } from '../../../shared/lib/format'
import { ErrorState } from '../../../shared/ui/ErrorState'
import { Loading } from '../../../shared/ui/Loading'
import { WAIT_FIELDS, waitBasis } from './waitConfig'
import { WaitEstimateCard } from './WaitEstimateCard'

export function WaitForecast({ hospital }: { hospital: string }) {
  const requestVersion = useRef(0)
  const [values, setValues] = useState<Record<string, string>>({})
  const { data, loading, error } = useRemote<WaitOptions>(
    hospital ? `/wait-options${query({ hospital, profile: values.bed_profile })}` : null,
  )
  const [result, setResult] = useState<WaitResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [submitError, setSubmitError] = useState('')
  useEffect(() => {
    if (!data) return
    setValues((previous) => {
      const next: Record<string, string> = {
        registration_dt: previous.registration_dt || data.default_date,
      }
      for (const [key] of WAIT_FIELDS) {
        const options = data.options[key] ?? []
        next[key] = options.includes(previous[key])
          ? previous[key]
          : options.includes(data.example[key])
            ? data.example[key]
            : (options[0] ?? '')
      }
      return next
    })
    setResult(null)
  }, [data])
  useEffect(
    () => () => {
      requestVersion.current += 1
    },
    [],
  )
  const setField = (field: string, value: string) => {
    requestVersion.current += 1
    setBusy(false)
    setValues((previous) => ({ ...previous, [field]: value }))
    setResult(null)
    setSubmitError('')
  }
  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    const version = ++requestVersion.current
    setBusy(true)
    setSubmitError('')
    setResult(null)
    try {
      const response = await post<WaitResult>('/predictions/wait', {
        ...values,
        hospital_id: hospitalId(hospital),
      })
      if (requestVersion.current === version) setResult(response)
    } catch (error) {
      if (requestVersion.current === version)
        setSubmitError(error instanceof Error ? error.message : 'Не удалось рассчитать прогноз.')
    } finally {
      if (requestVersion.current === version) setBusy(false)
    }
  }
  return (
    <>
      {loading && <Loading />}
      {error && <ErrorState message={error} />}
      {data && (
        <div className="wait-layout">
          <section className="panel wait-form-panel">
            <h2>Параметры направления</h2>
            <p>
              {data.method === 'catboost'
                ? 'Заполните параметры и нажмите «Рассчитать ожидание».'
                : 'Выберите профиль и нажмите «Рассчитать ожидание».'}
            </p>
            <form onSubmit={submit} className="wait-form">
              {WAIT_FIELDS.filter(
                ([key]) => key === 'bed_profile' || data.method === 'catboost',
              ).map(([key, label]) => (
                <label key={key} className={key === 'bed_profile' ? 'wait-profile' : undefined}>
                  {label}
                  {key === 'icd10_ref_diag_code' ? (
                    <>
                      <input
                        list="diagnosis-options"
                        value={values[key] ?? ''}
                        onChange={(event) => setField(key, event.target.value)}
                        required
                      />
                      <datalist id="diagnosis-options">
                        {data.options[key]?.map((value) => (
                          <option key={value} value={value} />
                        ))}
                      </datalist>
                    </>
                  ) : (
                    <select
                      title={values[key] ?? ''}
                      value={values[key] ?? ''}
                      onChange={(event) => setField(key, event.target.value)}
                      required
                    >
                      {(data.options[key] ?? []).map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                  )}
                  {key === 'bed_profile' && (values[key]?.length ?? 0) > 48 && (
                    <span className="wait-selected-profile" aria-hidden="true">
                      {values[key]}
                    </span>
                  )}
                </label>
              ))}
              {data.method === 'catboost' && (
                <label>
                  Дата регистрации
                  <input
                    type="date"
                    value={values.registration_dt ?? ''}
                    min={data.min_date}
                    max={data.default_date}
                    onChange={(event) => setField('registration_dt', event.target.value)}
                    required
                  />
                </label>
              )}
              <button className="primary-button full-button" disabled={busy || loading}>
                {busy ? 'Рассчитываем…' : 'Рассчитать ожидание'} <ArrowRight size={17} />
              </button>
              {submitError && <ErrorState message={submitError} />}
            </form>
          </section>
          <div className="wait-result-column">
            {result ? (
              <>
                <WaitEstimateCard result={result} />
                {result.contributions.length > 0 ? (
                  <details className="panel forecast-details">
                    <summary>Что повлияло на оценку</summary>
                    <div className="contribution-list">
                      {result.contributions.slice(0, 6).map((item) => (
                        <div key={item.feature}>
                          <span>{item.label}</span>
                          <strong className={item.contribution >= 0 ? 'positive' : 'negative'}>
                            {item.contribution >= 0 ? '+' : ''}
                            {decimal(item.contribution, 2)} дн.
                          </strong>
                        </div>
                      ))}
                    </div>
                    <p className="panel-footnote">
                      Вклады показывают связи, найденные моделью, а не доказанные причины.
                    </p>
                  </details>
                ) : (
                  <details className="panel forecast-details">
                    <summary>Как получена оценка</summary>
                    <p>{waitBasis(result.method)}</p>
                    <p>
                      Использованы только исходы, известные до {day(result.training_cutoff)} — более
                      поздние случаи оставлены для проверки.
                    </p>
                    <p className="panel-footnote">
                      Диагноз, цель направления и дата не меняют групповую оценку. Для этого метода
                      нет вкладов отдельных признаков.
                    </p>
                  </details>
                )}
              </>
            ) : (
              <section className="result-placeholder" role="status" aria-live="polite">
                <span className="placeholder-icon">
                  <Clock3 size={22} />
                </span>
                <h2>{busy ? 'Рассчитываем ожидание…' : 'Оценка пока не рассчитана'}</h2>
                <p>
                  {busy
                    ? 'Результат появится здесь.'
                    : 'Выберите параметры направления и запустите расчёт.'}
                </p>
              </section>
            )}
          </div>
        </div>
      )}
    </>
  )
}
