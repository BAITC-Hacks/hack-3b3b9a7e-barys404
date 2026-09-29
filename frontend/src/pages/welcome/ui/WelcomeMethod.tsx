import { t } from '../../../shared/lib/i18n'
import { useStaggeredEntrance } from '../../../shared/lib/useEntrance'

export function WelcomeMethod() {
  const entrance = useStaggeredEntrance<HTMLElement>()
  return (
    <section className="welcome-method" ref={entrance}>
      <div>
        <h2>{t('Что показывают данные')}</h2>
      </div>
      <article>
        <h3>{t('Направления')}</h3>
        <p>{t('Зарегистрированные обращения в выбранном периоде. Это не число занятых коек.')}</p>
      </article>
      <article>
        <h3>{t('Ожидание')}</h3>
        <p>
          {t('Наблюдаемый срок до госпитализации среди завершённых случаев, а не место в очереди.')}
        </p>
      </article>
      <article>
        <h3>{t('Прогноз')}</h3>
        <p>
          {t(
            'Оценка по историческим данным. Она помогает анализировать поток, но не назначает дату лечения.',
          )}{' '}
        </p>
      </article>
    </section>
  )
}
