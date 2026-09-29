import { GuideFaqItem } from './GuideFaqItem'
import { ArrowRight, BookOpen, Check, ChevronDown, Clock3, Expand, X } from 'lucide-react'
import { useRef, useState } from 'react'
import { t } from '../../../shared/lib/i18n'
import type { Mode, View } from '../../../shared/config/navigation'
import { PageHeading } from '../../../shared/ui/PageHeading'

const screenshots: Record<string, string> = {
  overview: new URL('../assets/overview.png', import.meta.url).href,
  filters: new URL('../assets/filters.png', import.meta.url).href,
  hospitals: new URL('../assets/hospitals.png', import.meta.url).href,
  hospital: new URL('../assets/hospital.png', import.meta.url).href,
  compare: new URL('../assets/compare.png', import.meta.url).href,
  forecasts: new URL('../assets/forecasts.png', import.meta.url).href,
  waiting: new URL('../assets/waiting.png', import.meta.url).href,
}
type Lesson = {
  id: string
  title: string
  intro: string
  instructions: string[]
  image: string
  caption: string
  action: string
  view: View
}

const faq = [
  [
    'Почему у меня нет раздела «Сравнение»?',
    'Разделы зависят от роли. Госорган видит список и сравнение стационаров. Аналитик больницы работает с данными своей организации. Если доступ выдан неверно, обратитесь к администратору.',
  ],
  [
    'Что делать, если данные не появились?',
    'Проверьте период, регион и профиль, затем нажмите «Применить». Если выборка пустая, расширьте период или нажмите «Сбросить». При сообщении об ошибке воспользуйтесь кнопкой повторной загрузки, если она доступна.',
  ],
  [
    'Почему кнопка «Применить» неактивна?',
    'Она становится доступной после изменения фильтров. Если вы ничего не меняли, на странице уже показана текущая выборка.',
  ],
  [
    'Это данные на сегодняшний день?',
    'Нет. В демо используются исторические данные за январь–март 2025 года. Прогноз потока относится к семи дням после конца истории, а не после сегодняшней даты.',
  ],
  [
    'Ожидание — это сколько осталось ждать пациенту?',
    'Нет. Это полный срок от регистрации направления до госпитализации по завершённым случаям. Медиана описывает историю, а расчёт во вкладке «Время ожидания» даёт оценку, которая может отличаться от фактического срока.',
  ],
  [
    'Можно ли по сравнению выбрать «лучшую» больницу?',
    'Сравнение не является рейтингом качества. Показатели не учитывают сложность случаев и коечную мощность. Используйте их как повод для дальнейшего анализа, а не как готовое решение.',
  ],
  [
    'Как сохранить результат в PDF?',
    'В карточке стационара или разделе «Сравнение» найдите блок «Сводка для обсуждения». Выберите вопрос, сформируйте сводку, просмотрите её и подтвердите проверку перед скачиванием PDF.',
  ],
  [
    'Почему цифры отличаются от скриншотов в обучении?',
    'Скриншоты показывают пример в русскоязычном кабинете госоргана и светлой теме. Ваши значения зависят от роли, выбранной больницы и фильтров; расположение блоков также меняется на телефоне.',
  ],
]

export function DataPage({ mode, go }: { mode: Mode; go: (view: View) => void }) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const [preview, setPreview] = useState<{ image: string; caption: string } | null>(null)
  const government = mode === 'government'
  const lessons: Lesson[] = [
    {
      id: 'overview',
      title: 'Начните с общей картины',
      intro: 'Откройте «Обзор»: здесь видно, сколько направлений поступило и как менялся поток.',
      instructions: [
        'Посмотрите период данных в верхней части кабинета.',
        'Сопоставьте график поступления с карточками показателей справа.',
        'Наведите указатель на график, чтобы увидеть значение за конкретную дату.',
      ],
      image: 'overview',
      caption: 'Обзор: фильтры сверху, динамика и ключевые показатели ниже.',
      action: 'Открыть обзор',
      view: 'overview',
    },
    {
      id: 'filters',
      title: 'Настройте свою выборку',
      intro:
        'Фильтры помогают ответить на конкретный вопрос — например, посмотреть один профиль за месяц.',
      instructions: [
        'Задайте даты «С» и «По» в блоке «Период регистрации».',
        'Выберите регион происхождения и профиль или оставьте все значения.',
        'Нажмите «Применить». Чтобы вернуться к исходной выборке, нажмите «Сбросить».',
      ],
      image: 'filters',
      caption: 'Измените параметры и примените их. Регион относится к происхождению направления.',
      action: 'Попробовать фильтры',
      view: 'overview',
    },
    {
      id: 'hospital',
      title: government ? 'Найдите нужную больницу' : 'Откройте свою больницу',
      intro: government
        ? 'В разделе «Стационары» можно перейти от общей картины к конкретной организации.'
        : 'Раздел «Моя больница» открывает карточку организации, закреплённой за вашим аккаунтом.',
      instructions: government
        ? [
            'Откройте «Стационары» в левом меню.',
            'Введите часть названия и нажмите кнопку с лупой или Enter.',
            'Нажмите на строку больницы, чтобы открыть её показатели и исходы.',
          ]
        : [
            'Откройте «Моя больница» в левом меню.',
            'Проверьте название организации и выбранный период.',
            'Изучите показатели и исходы; ниже доступна сводка для обсуждения.',
          ],
      image: government ? 'hospitals' : 'hospital',
      caption: government
        ? 'Поиск по названию расположен над списком. Строка открывает карточку стационара.'
        : 'Карточка стационара: показатели, исходы и переход к прогнозам.',
      action: government ? 'Найти стационар' : 'Открыть мою больницу',
      view: government ? 'hospitals' : 'hospital',
    },
    ...(government
      ? [
          {
            id: 'compare',
            title: 'Сравните стационары в одном контексте',
            intro:
              'Выберите до трёх организаций и сравните их за один период с одинаковыми фильтрами.',
            instructions: [
              'Откройте «Сравнение» и проверьте период, регион и профиль.',
              'Отметьте нужные организации слева. Чтобы выбрать другую, сначала снимите одну из трёх отметок.',
              'Посмотрите ожидание, число направлений и долю отказов в результатах справа.',
            ],
            image: 'compare',
            caption:
              'Выбор организаций слева связан с результатами справа. Это сравнение данных, а не рейтинг качества.',
            action: 'Перейти к сравнению',
            view: 'compare' as View,
          },
        ]
      : []),
    {
      id: 'forecasts',
      title: 'Посмотрите прогноз и оценку ожидания',
      intro:
        'В разделе «Прогнозы» два разных инструмента: поток новых направлений и оценка срока ожидания.',
      instructions: [
        government
          ? 'Проверьте выбранную больницу в верхнем поле «Стационар».'
          : 'Прогноз строится для вашей больницы.',
        'Во вкладке «Поток направлений» посмотрите оценку на семь дней и даты прогнозируемого периода.',
        'Для оценки срока откройте «Время ожидания», заполните доступные параметры и нажмите «Рассчитать ожидание».',
      ],
      image: 'forecasts',
      caption: 'Прогноз потока: ожидаемое число направлений и продолжение исторического графика.',
      action: 'Открыть прогнозы',
      view: 'forecasts',
    },
  ]

  const jump = (id: string) => {
    const section = document.getElementById(`guide-${id}`)
    section?.focus({ preventScroll: true })
    section?.scrollIntoView({ behavior: 'auto', block: 'start' })
  }
  const showImage = (image: string, caption: string) => {
    setPreview({ image, caption })
    dialogRef.current?.showModal()
  }
  const screenshot = (image: string, caption: string) => (
    <figure className="guide-figure">
      <button
        className="guide-screenshot"
        onClick={() => showImage(image, caption)}
        aria-label={`${t('Увеличить скриншот')}: ${t(caption)}`}
      >
        <img
          src={screenshots[image]}
          alt={t(caption)}
          loading="lazy"
          decoding="async"
          width="1130"
          height={image === 'filters' ? '220' : image === 'waiting' ? '650' : '760'}
        />
        <span className="guide-zoom">
          <Expand size={14} />
          {t('Увеличить')}
        </span>
      </button>
      <figcaption>{t(caption)}</figcaption>
    </figure>
  )

  return (
    <div className="guide-page">
      <PageHeading
        eyebrow={t('РУКОВОДСТВО')}
        title={t('Как начать работу')}
        description={t(
          'От первого обзора до прогноза — пройдите шаги и попробуйте каждый в своём кабинете.',
        )}
      />
      <section className="guide-start" aria-labelledby="guide-start-title">
        <div className="guide-start-copy">
          <span className="guide-duration">
            <BookOpen size={17} />
            {t('Знакомство с платформой')}
            <span>·</span>
            <Clock3 size={15} />
            {t('5 минут')}
          </span>
          <h2 id="guide-start-title">{t('Один маршрут, понятный результат')}</h2>
          <p>
            {t(
              government
                ? 'Ваш кабинет: госорган. Вы можете изучать общую картину, находить больницы и сравнивать организации.'
                : 'Ваш кабинет: больница. Вы работаете с показателями и прогнозами своей организации.',
            )}
          </p>
          <button className="primary-button" onClick={() => jump('overview')}>
            {t('Начать обучение')}
            <ArrowRight size={17} />
          </button>
        </div>
        <ol className="guide-route" aria-label={t('Шаги обучения')}>
          {lessons.map((lesson, index) => (
            <li key={lesson.id}>
              <button onClick={() => jump(lesson.id)}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                {t(lesson.title)}
                <ArrowRight size={16} />
              </button>
            </li>
          ))}
          <li>
            <button onClick={() => jump('faq')}>
              <span>?</span>
              {t('Частые вопросы')}
              <ArrowRight size={16} />
            </button>
          </li>
        </ol>
      </section>
      <p className="guide-image-note">
        {t(
          'Скриншоты — примеры из демо в светлой теме, на русском языке. Нажмите на изображение, чтобы рассмотреть детали.',
        )}
      </p>
      <div className="guide-lessons">
        {lessons.map((lesson, index) => (
          <section
            className={`guide-lesson guide-lesson--${lesson.id}`}
            id={`guide-${lesson.id}`}
            key={lesson.id}
            tabIndex={-1}
            aria-labelledby={`guide-title-${lesson.id}`}
          >
            <div className="guide-lesson-copy">
              <span className="guide-step">
                {String(index + 1).padStart(2, '0')}
                <span>{t('ШАГ')}</span>
              </span>
              <h2 id={`guide-title-${lesson.id}`}>{t(lesson.title)}</h2>
              <p>{t(lesson.intro)}</p>
              <ol className="guide-instructions">
                {lesson.instructions.map((instruction) => (
                  <li key={instruction}>{t(instruction)}</li>
                ))}
              </ol>
              <button className="guide-action" onClick={() => go(lesson.view)}>
                {t(lesson.action)}
                <ArrowRight size={16} />
              </button>
            </div>
            <div className="guide-lesson-media">
              {screenshot(lesson.image, lesson.caption)}
              {lesson.id === 'forecasts' && (
                <details className="guide-wait-example">
                  <summary>
                    {t('Где рассчитать время ожидания?')}
                    <ChevronDown size={17} />
                  </summary>
                  {screenshot(
                    'waiting',
                    'Вкладка «Время ожидания»: параметры направления и кнопка расчёта.',
                  )}
                </details>
              )}
            </div>
          </section>
        ))}
      </div>
      <section className="guide-ready">
        <span className="guide-ready-icon">
          <Check size={22} />
        </span>
        <div>
          <h2>{t('Теперь попробуйте сами')}</h2>
          <p>
            {t(
              'Откройте обзор, задайте период и найдите один показатель, который хотите изучить подробнее.',
            )}
          </p>
        </div>
        <button className="secondary-button" onClick={() => go('overview')}>
          {t('Перейти в кабинет')}
          <ArrowRight size={17} />
        </button>
      </section>
      <section className="guide-faq" id="guide-faq" tabIndex={-1} aria-labelledby="guide-faq-title">
        <div className="guide-faq-heading">
          <span className="section-kicker">FAQ</span>
          <h2 id="guide-faq-title">{t('Частые вопросы')}</h2>
          <p>{t('Если что-то осталось непонятным — начните здесь.')}</p>
        </div>
        <div className="guide-faq-list">
          {faq.map(([question, answer]) => (
            <GuideFaqItem key={question} question={t(question)} answer={t(answer)} />
          ))}
        </div>
      </section>
      <dialog
        ref={dialogRef}
        className="guide-dialog"
        aria-labelledby="guide-preview-title"
        onClick={(event) => {
          if (event.target === event.currentTarget) dialogRef.current?.close()
        }}
      >
        <div className="guide-dialog-heading">
          <h2 id="guide-preview-title">{t('Скриншот интерфейса')}</h2>
          <button
            autoFocus
            className="icon-button"
            onClick={() => dialogRef.current?.close()}
            aria-label={t('Закрыть скриншот')}
          >
            <X size={22} />
          </button>
        </div>
        {preview && (
          <>
            <div className="guide-dialog-image">
              <img src={screenshots[preview.image]} alt={t(preview.caption)} />
            </div>
            <p>
              {t(preview.caption)} {t('На небольшом экране изображение можно прокручивать.')}
            </p>
          </>
        )}
      </dialog>
    </div>
  )
}
