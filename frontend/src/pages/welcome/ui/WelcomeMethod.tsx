import { useStaggeredEntrance } from '../../../shared/lib/useEntrance'

export function WelcomeMethod() {
  const entrance = useStaggeredEntrance<HTMLElement>()
  return (
    <section className="welcome-method" ref={entrance}>
      <div>
        <h2>Что показывают данные</h2>
      </div>
      <article>
        <h3>Направления</h3>
        <p>Зарегистрированные обращения в выбранном периоде. Это не число занятых коек.</p>
      </article>
      <article>
        <h3>Ожидание</h3>
        <p>Наблюдаемый срок до госпитализации среди завершённых случаев, а не место в очереди.</p>
      </article>
      <article>
        <h3>Прогноз</h3>
        <p>
          Оценка по историческим данным. Она помогает анализировать поток, но не назначает дату
          лечения.
        </p>
      </article>
    </section>
  )
}
