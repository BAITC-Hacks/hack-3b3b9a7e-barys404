/** Analyst-facing text. Source values and hospital names stay unchanged in API requests. */
export const analyticsMessages: Record<string, { kk: string; en: string }> = {
  'Обзор больницы': { kk: 'Ауруханаға шолу', en: 'Hospital overview' },
  'Обзор направлений': { kk: 'Жолдамаларға шолу', en: 'Referral overview' },
  'Поступление направлений и результаты госпитализации.': {
    kk: 'Түскен жолдамалар мен ауруханаға жатқызу нәтижелері.',
    en: 'Incoming referrals and hospitalization outcomes.',
  },
  'Регион происхождения: {region}.': {
    kk: 'Жолдама берілген өңір: {region}.',
    en: 'Region of origin: {region}.',
  },
  'Исторические данные · 2025': { kk: 'Тарихи деректер · 2025', en: 'Historical data · 2025' },
  'По этим фильтрам записей нет': {
    kk: 'Бұл сүзгілер бойынша жазба жоқ',
    en: 'No records match these filters',
  },
  'Выберите другой регион или профиль либо сбросьте фильтры над обзором.': {
    kk: 'Басқа өңірді немесе бейінді таңдаңыз, не шолудың үстіндегі сүзгілерді тазалаңыз.',
    en: 'Choose another region or specialty, or reset the filters above.',
  },
  'Карточка больницы': { kk: 'Аурухана карточкасы', en: 'Hospital details' },
  'Профили направлений, наблюдаемое ожидание и прогноз входящего потока находятся в одной карточке.':
    {
      kk: 'Жолдама бейіндері, тіркелген күту уақыты және түсетін жолдамалар болжамы бір карточкада берілген.',
      en: 'Referral specialties, observed waiting times and the incoming referral forecast in one place.',
    },
  'Открыть карточку': { kk: 'Карточканы ашу', en: 'View details' },
  СТАЦИОНАРЫ: { kk: 'СТАЦИОНАРЛАР', en: 'HOSPITALS' },
  'Найдите нужную больницу': { kk: 'Қажетті аурухананы табыңыз', en: 'Find a hospital' },
  'Откройте организацию, чтобы увидеть её профиль, исходы и прогноз.': {
    kk: 'Бейінін, нәтижелерін және болжамын көру үшін ұйымды ашыңыз.',
    en: 'Open an organization to see its specialties, outcomes and forecast.',
  },
  'Название стационара': { kk: 'Стационар атауы', en: 'Hospital name' },
  'Поиск стационара': { kk: 'Стационарды іздеу', en: 'Search hospitals' },
  Поиск: { kk: 'Іздеу', en: 'Search' },
  'Список ограничен фильтрами:': {
    kk: 'Тізімге қолданылған сүзгілер:',
    en: 'Filters applied to this list:',
  },
  '. Сбросить их можно кнопкой выше.': {
    kk: '. Оларды жоғарыдағы батырмамен тазалауға болады.',
    en: '. Reset them using the button above.',
  },
  Стационар: { kk: 'Стационар', en: 'Hospital' },
  Направления: { kk: 'Жолдамалар', en: 'Referrals' },
  Ожидание: { kk: 'Күту уақыты', en: 'Waiting time' },
  Отказы: { kk: 'Бас тартулар', en: 'Refusals' },
  'Показаны {start}–{end} из {total}': {
    kk: 'Барлығы {total}, көрсетілгені: {start}–{end}',
    en: 'Showing {start}–{end} of {total}',
  },
  Назад: { kk: 'Артқа', en: 'Previous' },
  Далее: { kk: 'Келесі', en: 'Next' },
  'Стационары не найдены': { kk: 'Стационарлар табылмады', en: 'No hospitals found' },
  'Попробуйте другое название или сбросьте фильтры.': {
    kk: 'Басқа атауды енгізіңіз немесе сүзгілерді тазалаңыз.',
    en: 'Try another name or reset the filters.',
  },
  'Медиана показана только при достаточном числе завершённых госпитализаций. Доля отказов считается среди известных исходов.':
    {
      kk: 'Медиана аяқталған жатқызу жағдайлары жеткілікті болғанда ғана көрсетіледі. Бас тартулар үлесі нәтижесі белгілі жағдайлар бойынша есептеледі.',
      en: 'The median is shown only when enough completed hospitalizations are available. The refusal share is calculated among known outcomes.',
    },
  'К списку стационаров': { kk: 'Стационарлар тізіміне', en: 'Back to hospitals' },
  'КАРТОЧКА СТАЦИОНАРА': { kk: 'СТАЦИОНАР КАРТОЧКАСЫ', en: 'HOSPITAL DETAILS' },
  'Наблюдаемые показатели по выбранному периоду и профилю.': {
    kk: 'Таңдалған кезең мен бейін бойынша тіркелген көрсеткіштер.',
    en: 'Observed metrics for the selected period and specialty.',
  },
  Сравнить: { kk: 'Салыстыру', en: 'Compare' },
  'Открыть прогноз': { kk: 'Болжамды ашу', en: 'View forecast' },
  'Нет записей для выбранных фильтров': {
    kk: 'Таңдалған сүзгілер бойынша жазба жоқ',
    en: 'No records for the selected filters',
  },
  'Измените период, регион или профиль, чтобы увидеть показатели стационара.': {
    kk: 'Стационар көрсеткіштерін көру үшін кезеңді, өңірді немесе бейінді өзгертіңіз.',
    en: 'Change the period, region or specialty to see hospital metrics.',
  },
  'За выбранный период': { kk: 'Таңдалған кезеңде', en: 'In the selected period' },
  'Медиана ожидания': { kk: 'Күту медианасы', en: 'Median waiting time' },
  дня: { kk: 'күн', en: 'days' },
  'По завершённым случаям': { kk: 'Аяқталған жағдайлар бойынша', en: 'Among completed cases' },
  '90% ожидали до': { kk: '90% үшін күту шегі', en: '90% waited up to' },
  'Наблюдаемый P90': { kk: 'Тіркелген P90', en: 'Observed P90' },
  'Доля отказов': { kk: 'Бас тартулар үлесі', en: 'Refusal share' },
  'Среди известных исходов': { kk: 'Нәтижесі белгілі жағдайларда', en: 'Among known outcomes' },
  ПОСТУПЛЕНИЕ: { kk: 'ТҮСКЕН ЖОЛДАМАЛАР', en: 'INCOMING REFERRALS' },
  'Направления по неделям': { kk: 'Апталар бойынша жолдамалар', en: 'Weekly referrals' },
  'История выбранного стационара': {
    kk: 'Таңдалған стационар тарихы',
    en: 'History of the selected hospital',
  },
  ПРОФИЛИ: { kk: 'БЕЙІНДЕР', en: 'SPECIALTIES' },
  'Что поступает чаще': {
    kk: 'Қай бейінге жолдама жиі түседі',
    en: 'Most common referral specialties',
  },
  'Восемь наиболее частых профилей': {
    kk: 'Ең жиі кездесетін сегіз бейін',
    en: 'Eight most common specialties',
  },
  'Не указан': { kk: 'Көрсетілмеген', en: 'Not specified' },
  ПРОГНОЗ: { kk: 'БОЛЖАМ', en: 'FORECAST' },
  'Что ожидается дальше?': { kk: 'Алда не күтіледі?', en: 'What comes next?' },
  'Для этого стационара можно посмотреть прогноз входящих направлений на семь дней после последней даты в данных.':
    {
      kk: 'Осы стационар үшін деректердегі соңғы күннен кейінгі жеті күнге түсетін жолдамалар болжамын көруге болады.',
      en: 'View this hospital’s incoming referral forecast for the seven days after the last date in the data.',
    },
  'Показать прогноз': { kk: 'Болжамды көрсету', en: 'Show forecast' },
  'P90 — наблюдённый срок у 90% завершённых случаев, а не доверительный интервал. Фильтры выше не меняют обученную модель прогноза.':
    {
      kk: 'P90 — аяқталған жағдайлардың 90%-ындағы күту уақытының шегі, сенімділік аралығы емес. Жоғарыдағы сүзгілер оқытылған болжам моделін өзгертпейді.',
      en: 'P90 is the observed waiting-time threshold for 90% of completed cases, not a confidence interval. The filters above do not change the trained forecasting model.',
    },
  СРАВНЕНИЕ: { kk: 'САЛЫСТЫРУ', en: 'COMPARISON' },
  'Сопоставьте стационары': { kk: 'Стационарларды салыстырыңыз', en: 'Compare hospitals' },
  'Выберите до трёх организаций за один период и с одинаковыми фильтрами.': {
    kk: 'Бір кезең мен бірдей сүзгілер бойынша үш ұйымға дейін таңдаңыз.',
    en: 'Choose up to three organizations for the same period and filters.',
  },
  'Сравнение описывает данные, но не учитывает сложность случаев и коечную мощность. Оно не является рейтингом качества больниц.':
    {
      kk: 'Салыстыру деректерді сипаттайды, бірақ жағдайлардың күрделілігі мен төсек қуатын ескермейді. Бұл ауруханалар сапасының рейтингі емес.',
      en: 'This comparison describes the data without adjusting for case complexity or bed capacity. It is not a hospital quality ranking.',
    },
  'Часть выбранных организаций не проходит текущие фильтры или минимум 30 направлений. В сводку войдут только видимые результаты.':
    {
      kk: 'Кейбір таңдалған ұйымдар ағымдағы сүзгілерге немесе кемінде 30 жолдама талабына сай емес. Есепке тек көрсетілген нәтижелер кіреді.',
      en: 'Some selected organizations do not match the current filters or the minimum of 30 referrals. Only visible results will be included in the briefing.',
    },
  'Снять скрытый выбор': { kk: 'Жасырын таңдауларды алып тастау', en: 'Clear hidden selections' },
  'Прогноз направлений': { kk: 'Жолдамалар болжамы', en: 'Referral forecast' },
  'Оценка ожидания': { kk: 'Күту уақытын бағалау', en: 'Waiting-time estimate' },
  'Стационар: {hospital}.': { kk: 'Стационар: {hospital}.', en: 'Hospital: {hospital}.' },
  'Сколько направлений может поступить за следующие семь дней после конца данных.': {
    kk: 'Деректердегі соңғы күннен кейінгі жеті күнде қанша жолдама түсуі мүмкін.',
    en: 'How many referrals may arrive in the seven days after the data ends.',
  },
  'Оценка срока от регистрации направления до госпитализации по историческим данным.': {
    kk: 'Тарихи деректер негізінде жолдаманы тіркеуден ауруханаға жатқызуға дейінгі уақытты бағалау.',
    en: 'An estimate of the time from referral registration to hospitalization, based on historical data.',
  },
  'Тип прогноза': { kk: 'Болжам түрі', en: 'Forecast type' },
  'Поток направлений': { kk: 'Жолдамалар ағыны', en: 'Referral flow' },
  'Время ожидания': { kk: 'Күту уақыты', en: 'Waiting time' },
  'Стационар не выбран': { kk: 'Стационар таңдалмаған', en: 'No hospital selected' },
  'Откройте список стационаров и выберите организацию.': {
    kk: 'Стационарлар тізімін ашып, ұйымды таңдаңыз.',
    en: 'Open the hospital list and choose an organization.',
  },
  'Карточка и PDF-сводка': {
    kk: 'Карточка және PDF есебі',
    en: 'Hospital details and PDF briefing',
  },
  МЕТОДОЛОГИЯ: { kk: 'ӘДІСТЕМЕ', en: 'METHODOLOGY' },
  'Как читать показатели': {
    kk: 'Көрсеткіштерді қалай түсінуге болады',
    en: 'Understanding the metrics',
  },
  'Что означают цифры в кабинете и какие выводы можно из них делать.': {
    kk: 'Кабинеттегі сандар нені білдіреді және олардан қандай қорытынды жасауға болады.',
    en: 'What the figures mean and which conclusions they support.',
  },
  'ТРИ ОСНОВНЫХ ПОНЯТИЯ': { kk: 'ҮШ НЕГІЗГІ ҰҒЫМ', en: 'THREE KEY CONCEPTS' },
  'Зарегистрированные направления в выбранном периоде. Динамика не показывает свободные койки или нагрузку на персонал.':
    {
      kk: 'Таңдалған кезеңде тіркелген жолдамалар. Олардың өзгерісі бос төсек санын немесе қызметкерлер жүктемесін көрсетпейді.',
      en: 'Referrals registered during the selected period. Their trend does not show available beds or staff workload.',
    },
  'Полный срок от регистрации до госпитализации среди завершённых случаев. Это не оставшееся время ожидания конкретного пациента.':
    {
      kk: 'Аяқталған жағдайларда тіркеуден ауруханаға жатқызуға дейінгі толық уақыт. Бұл нақты пациенттің қалған күту уақыты емес.',
      en: 'The full time from registration to hospitalization among completed cases. This is not an individual patient’s remaining waiting time.',
    },
  'Прогноз потока': { kk: 'Жолдамалар ағынының болжамы', en: 'Flow forecast' },
  'Оценка новых направлений на семь дней после последней даты в истории. Прогноз не описывает сегодняшнюю очередь.':
    {
      kk: 'Тарихтағы соңғы күннен кейінгі жеті күнге жаңа жолдамалар санын бағалау. Болжам бүгінгі кезекті сипаттамайды.',
      en: 'Estimated new referrals for seven days after the last historical date. The forecast does not describe today’s queue.',
    },
  'Общая ошибка оценки ожидания': {
    kk: 'Күту бағасының жалпы қатесі',
    en: 'Overall waiting-time error',
  },
  'На исторической проверке; ошибка отдельных групп может отличаться': {
    kk: 'Тарихи тексеру бойынша; жеке топтардың қатесі өзгеше болуы мүмкін',
    en: 'On historical validation; errors may differ by group',
  },
  'Общая ошибка прогноза потока': {
    kk: 'Ағын болжамының жалпы қатесі',
    en: 'Overall flow forecast error',
  },
  'напр.': { kk: 'жолд.', en: 'ref.' },
  'На организацию в день в историческом тесте': {
    kk: 'Тарихи тестте бір ұйымға бір күнге',
    en: 'Per organization per day in the historical test',
  },
  'Данные относятся к январю–марту 2025 года. Сравнение не учитывает сложность случаев и мощность больниц. Модель помогает анализировать историю; решения принимает специалист.':
    {
      kk: 'Деректер 2025 жылғы қаңтар–наурызға жатады. Салыстыру жағдайлардың күрделілігі мен аурухана қуатын ескермейді. Модель тарихты талдауға көмектеседі; шешімді маман қабылдайды.',
      en: 'The data covers January–March 2025. Comparisons do not adjust for case complexity or hospital capacity. The model supports historical analysis; a specialist makes the decisions.',
    },
  'Рост направлений': { kk: 'Жолдамалар санының өсуі', en: 'Growth in referrals' },
  'Последние два полных периода по 7 дней': {
    kk: 'Соңғы екі толық 7 күндік кезең',
    en: 'The last two complete 7-day periods',
  },
  направлений: { kk: 'жолдама', en: 'referrals' },
  'За этот период нет роста с достаточным числом наблюдений.': {
    kk: 'Бұл кезеңде бақылаулар саны жеткілікті топтарда өсім жоқ.',
    en: 'No growth with sufficient observations in this period.',
  },
  'Рост записанного потока — повод проверить данные и ситуацию, а не оценка занятости коек.': {
    kk: 'Тіркелген ағынның өсуі деректер мен жағдайды тексеруге негіз болады, бірақ төсектердің толуын бағаламайды.',
    en: 'Growth in recorded referrals is a reason to check the data and situation, not a measure of bed occupancy.',
  },
  'Исходы направлений': { kk: 'Жолдама нәтижелері', en: 'Referral outcomes' },
  'По записям в выгрузке': {
    kk: 'Жүктелген жазбалар бойынша',
    en: 'As recorded in the source data',
  },
  Госпитализации: { kk: 'Ауруханаға жатқызулар', en: 'Hospitalizations' },
  'Исход не записан': { kk: 'Нәтиже тіркелмеген', en: 'Outcome not recorded' },
  'Отсутствие исхода в выгрузке не означает, что человек ожидает сейчас.': {
    kk: 'Деректерде нәтиженің болмауы адамның қазір кезекте тұрғанын білдірмейді.',
    en: 'A missing outcome in the data does not mean the person is currently waiting.',
  },
  'Зарегистрировано за период': { kk: 'Кезең ішінде тіркелген', en: 'Registered in this period' },
  Стационары: { kk: 'Стационарлар', en: 'Hospitals' },
  'С направлениями в выборке': {
    kk: 'Іріктемеде жолдамалары бар',
    en: 'With referrals in the selection',
  },
  'По завершённым госпитализациям': {
    kk: 'Аяқталған жатқызулар бойынша',
    en: 'Among completed hospitalizations',
  },
  'С известным исходом': { kk: 'Нәтижесі белгілі', en: 'With a known outcome' },
  'Стационары по числу направлений': {
    kk: 'Жолдама саны бойынша стационарлар',
    en: 'Hospitals by referral count',
  },
  'Все стационары': { kk: 'Барлық стационарлар', en: 'All hospitals' },
  Организация: { kk: 'Ұйым', en: 'Organization' },
  'Поступление направлений': { kk: 'Жолдамалардың түсуі', en: 'Incoming referrals' },
  'По неделям регистрации': { kk: 'Тіркеу аптасы бойынша', en: 'By registration week' },
  'дн.': { kk: 'күн', en: 'days' },
  ВЫБОР: { kk: 'ТАҢДАУ', en: 'SELECTION' },
  Организации: { kk: 'Ұйымдар', en: 'Organizations' },
  'До трёх стационаров': { kk: 'Үш стационарға дейін', en: 'Up to three hospitals' },
  'Найти организацию': { kk: 'Ұйымды табу', en: 'Find an organization' },
  'Найти организацию для сравнения': {
    kk: 'Салыстыру үшін ұйымды табу',
    en: 'Find an organization to compare',
  },
  'Загружаем организации…': { kk: 'Ұйымдар жүктелуде…', en: 'Loading organizations…' },
  'ОДИН ПЕРИОД · ОДИН КОНТЕКСТ': {
    kk: 'БІР КЕЗЕҢ · БІРДЕЙ ШАРТТАР',
    en: 'SAME PERIOD · SAME CONTEXT',
  },
  'Наблюдаемое ожидание': { kk: 'Тіркелген күту уақыты', en: 'Observed waiting time' },
  'Медиана по завершённым госпитализациям': {
    kk: 'Аяқталған жатқызулар бойынша медиана',
    en: 'Median among completed hospitalizations',
  },
  'направлений · отказы': { kk: 'жолдама · бас тартулар', en: 'referrals · refusals' },
  'Выберите стационары': { kk: 'Стационарларды таңдаңыз', en: 'Choose hospitals' },
  'Отметьте от одной до трёх организаций слева.': {
    kk: 'Сол жақтан бірден үшке дейін ұйымды белгілеңіз.',
    en: 'Select one to three organizations on the left.',
  },
  'Рассчитываем прогноз': { kk: 'Болжам есептелуде', en: 'Calculating forecast' },
  'направлений за 7 дней': { kk: 'жолдама, 7 күнде', en: 'referrals over 7 days' },
  'Последнее наблюдение:': { kk: 'Соңғы бақылау:', en: 'Last observation:' },
  'По историческим данным': { kk: 'Тарихи деректер бойынша', en: 'Based on historical data' },
  'История и следующие семь дней': {
    kk: 'Тарих және одан кейінгі жеті күн',
    en: 'History and the next seven days',
  },
  Наблюдения: { kk: 'Бақылаулар', en: 'Observed' },
  Прогноз: { kk: 'Болжам', en: 'Forecast' },
  'Прогноз показывает входящие направления, а не занятость коек или текущую очередь. Он не изменяет очередь и не назначает лечение.':
    {
      kk: 'Болжам түсетін жолдамаларды көрсетеді, төсектердің толуын немесе қазіргі кезекті емес. Ол кезекті өзгертпейді және ем тағайындамайды.',
      en: 'The forecast shows incoming referrals, not bed occupancy or the current queue. It does not change the queue or prescribe treatment.',
    },
  'Прогноз по дням': { kk: 'Күндер бойынша болжам', en: 'Daily forecast' },
  'день {day}': { kk: '{day}-күн', en: 'day {day}' },
  'Средняя ошибка на проверке': { kk: 'Тексерудегі орташа қате', en: 'Average validation error' },
  направления: { kk: 'жолдама', en: 'referrals' },
  'Средняя абсолютная ошибка на историческом тесте для организации в день. На первом дне горизонта ошибка выше: {mae}.':
    {
      kk: 'Тарихи тестте бір ұйымға бір күнге есептелген орташа абсолюттік қате. Болжамның бірінші күнінде қате жоғары: {mae}.',
      en: 'Mean absolute error per organization per day on the historical test. The error is higher on the first forecast day: {mae}.',
    },
  'Простой прогноз: {mae} направления': {
    kk: 'Қарапайым болжам қатесі: {mae} жолдама',
    en: 'Baseline forecast error: {mae} referrals',
  },
  'Типичное время ожидания': { kk: 'Әдеттегі күту уақыты', en: 'Typical waiting time' },
  'Оценка недоступна': { kk: 'Баға қолжетімсіз', en: 'Estimate unavailable' },
  'Общий срок до госпитализации, не оставшееся время в очереди.': {
    kk: 'Бұл ауруханаға жатқызуға дейінгі толық уақыт, кезекте қалған уақыт емес.',
    en: 'The total time to hospitalization, not the remaining time in the queue.',
  },
  случаев: { kk: 'жағдай', en: 'cases' },
  'Это групповая медиана, не индивидуальный срок.': {
    kk: 'Бұл жеке адамның мерзімі емес, топ медианасы.',
    en: 'This is a group median, not an individual waiting time.',
  },
  'Ошибка для этой больницы и профиля: {mae} дня на {count} более поздних случаях.': {
    kk: 'Осы аурухана мен бейін бойынша кейінгі {count} жағдайдағы қате: {mae} күн.',
    en: 'Error for this hospital and specialty: {mae} days across {count} later cases.',
  },
  'Общая ошибка на проверке: {mae} дня. Для этой группы отдельная ошибка не оценена.': {
    kk: 'Тексерудегі жалпы қате: {mae} күн. Бұл топтың қатесі бөлек бағаланбаған.',
    en: 'Overall validation error: {mae} days. This group’s error has not been assessed separately.',
  },
  'Это не дата госпитализации. Оценка не изменяет очередь и не назначает лечение.': {
    kk: 'Бұл ауруханаға жатқызу күні емес. Баға кезекті өзгертпейді және ем тағайындамайды.',
    en: 'This is not a hospitalization date. The estimate does not change the queue or prescribe treatment.',
  },
  'Не удалось рассчитать прогноз.': {
    kk: 'Болжамды есептеу мүмкін болмады.',
    en: 'The forecast could not be calculated.',
  },
  'Параметры направления': { kk: 'Жолдама параметрлері', en: 'Referral details' },
  'Заполните параметры и нажмите «Рассчитать ожидание».': {
    kk: 'Параметрлерді толтырып, «Күту уақытын есептеу» батырмасын басыңыз.',
    en: 'Enter the details and select “Estimate waiting time”.',
  },
  'Выберите профиль и нажмите «Рассчитать ожидание».': {
    kk: 'Бейінді таңдап, «Күту уақытын есептеу» батырмасын басыңыз.',
    en: 'Choose a specialty and select “Estimate waiting time”.',
  },
  'Дата регистрации': { kk: 'Тіркелген күні', en: 'Registration date' },
  'Рассчитываем…': { kk: 'Есептелуде…', en: 'Calculating…' },
  'Рассчитать ожидание': { kk: 'Күту уақытын есептеу', en: 'Estimate waiting time' },
  'Что повлияло на оценку': { kk: 'Бағаға не әсер етті', en: 'What influenced this estimate' },
  'Вклады показывают связи, найденные моделью, а не доказанные причины.': {
    kk: 'Үлестер дәлелденген себептерді емес, модель тапқан байланыстарды көрсетеді.',
    en: 'Contributions show associations found by the model, not proven causes.',
  },
  'Как получена оценка': { kk: 'Баға қалай алынды', en: 'How this estimate was calculated' },
  'Использованы только исходы, известные до {date} — более поздние случаи оставлены для проверки.':
    {
      kk: 'Тек {date} күніне дейін белгілі болған нәтижелер пайдаланылды; кейінгі жағдайлар тексеруге қалдырылды.',
      en: 'Only outcomes known before {date} were used; later cases were reserved for validation.',
    },
  'Диагноз, цель направления и дата не меняют групповую оценку. Для этого метода нет вкладов отдельных признаков.':
    {
      kk: 'Диагноз, жолдама мақсаты мен күні топтық бағаны өзгертпейді. Бұл әдісте жеке белгілердің үлесі есептелмейді.',
      en: 'Diagnosis, referral purpose and date do not change the group estimate. Individual feature contributions are not available for this method.',
    },
  'Рассчитываем ожидание…': { kk: 'Күту уақыты есептелуде…', en: 'Estimating waiting time…' },
  'Оценка пока не рассчитана': { kk: 'Баға әлі есептелмеген', en: 'No estimate yet' },
  'Результат появится здесь.': {
    kk: 'Нәтиже осы жерде көрсетіледі.',
    en: 'The result will appear here.',
  },
  'Выберите параметры направления и запустите расчёт.': {
    kk: 'Жолдама параметрлерін таңдап, есептеуді бастаңыз.',
    en: 'Choose the referral details and run the estimate.',
  },
  'Период регистрации': { kk: 'Тіркеу кезеңі', en: 'Registration period' },
  С: { kk: 'Басталуы', en: 'From' },
  По: { kk: 'Аяқталуы', en: 'To' },
  'Регион происхождения': { kk: 'Жолдама берілген өңір', en: 'Region of origin' },
  'Все регионы': { kk: 'Барлық өңірлер', en: 'All regions' },
  Профиль: { kk: 'Бейін', en: 'Specialty' },
  'Все профили': { kk: 'Барлық бейіндер', en: 'All specialties' },
  'Сбросить фильтры': { kk: 'Сүзгілерді тазалау', en: 'Reset filters' },
  Сбросить: { kk: 'Тазалау', en: 'Reset' },
  'Выбрать стационар': { kk: 'Стационарды таңдау', en: 'Choose a hospital' },
  'Найти стационар': { kk: 'Стационарды табу', en: 'Find a hospital' },
  'Ничего не найдено': { kk: 'Ештеңе табылмады', en: 'No results found' },
  'Подготовка…': { kk: 'Дайындалуда…', en: 'Preparing…' },
  'Обновить просмотр': { kk: 'Алдын ала қарауды жаңарту', en: 'Refresh preview' },
  'Подготовить просмотр': { kk: 'Алдын ала қарауды дайындау', en: 'Prepare preview' },
  'Скачать PDF-сводку': { kk: 'PDF есебін жүктеп алу', en: 'Download PDF briefing' },
  'ПРОВЕРКА СПЕЦИАЛИСТОМ': { kk: 'МАМАННЫҢ ТЕКСЕРУІ', en: 'SPECIALIST REVIEW' },
  'Сводка для обсуждения': { kk: 'Талқылауға арналған есеп', en: 'Briefing for discussion' },
  'Период регистрации: {start} — {end}. Профиль: {profile}. Регион происхождения: {region}.': {
    kk: 'Тіркеу кезеңі: {start} — {end}. Бейін: {profile}. Жолдама берілген өңір: {region}.',
    en: 'Registration period: {start} — {end}. Specialty: {profile}. Region of origin: {region}.',
  },
  все: { kk: 'барлығы', en: 'all' },
  'Вопрос для проверки': { kk: 'Тексеру сұрағы', en: 'Review question' },
  'Поток направлений и доступная мощность': {
    kk: 'Жолдамалар ағыны және қолжетімді қуат',
    en: 'Referral flow and available capacity',
  },
  'Различия наблюдаемого ожидания': {
    kk: 'Тіркелген күту уақытындағы айырмашылықтар',
    en: 'Differences in observed waiting times',
  },
  'Причины отказов и полнота регистрации': {
    kk: 'Бас тарту себептері және тіркеудің толықтығы',
    en: 'Reasons for refusals and completeness of records',
  },
  'Выберите хотя бы один стационар.': {
    kk: 'Кемінде бір стационарды таңдаңыз.',
    en: 'Choose at least one hospital.',
  },
  'PDF содержит агрегаты и общие метрики моделей. Подтверждение означает просмотр аналитиком, а не формальное согласование решения или назначение лечения.':
    {
      kk: 'PDF жиынтық деректер мен модельдердің жалпы көрсеткіштерін қамтиды. Растау шешімді ресми мақұлдауды немесе ем тағайындауды емес, аналитиктің қарап шыққанын білдіреді.',
      en: 'The PDF contains aggregates and overall model metrics. Confirmation records the analyst’s review, not formal approval of a decision or a treatment prescription.',
    },
  'PDF-сводка формируется на русском языке.': {
    kk: 'PDF есебі орыс тілінде жасалады.',
    en: 'The PDF briefing is generated in Russian.',
  },
  'Проверьте содержимое PDF': { kk: 'PDF мазмұнын тексеріңіз', en: 'Review the PDF contents' },
  'Медиана, дни': { kk: 'Медиана, күн', en: 'Median, days' },
  'P90, дни': { kk: 'P90, күн', en: 'P90, days' },
  'Отказы, %': { kk: 'Бас тартулар, %', en: 'Refusals, %' },
  'Минимум группы и статистик: {minimum}. Прочерк означает недостаточно наблюдений. P90 — описательный квантиль ожидания, не интервал прогноза.':
    {
      kk: 'Топ пен статистика үшін ең аз саны: {minimum}. Сызықша бақылаулар жеткіліксіз екенін білдіреді. P90 — күту уақытының сипаттамалық квантилі, болжам аралығы емес.',
      en: 'Minimum group size for statistics: {minimum}. A dash means insufficient observations. P90 describes the waiting-time distribution; it is not a prediction interval.',
    },
  'Ожидание, дни': { kk: 'Күту уақыты, күн', en: 'Waiting time, days' },
  'Поток, направления / организацию в день': {
    kk: 'Ағын, бір ұйымға күніне жолдамалар',
    en: 'Flow, referrals per organization per day',
  },
  'MAE {mae}, базовый прогноз {baseline}. Версия {version}; тест {period}.': {
    kk: 'MAE {mae}, базалық болжам {baseline}. Нұсқа {version}; тест {period}.',
    en: 'MAE {mae}, baseline {baseline}. Version {version}; test {period}.',
  },
  'Актуальные метрики недоступны.': {
    kk: 'Өзекті көрсеткіштер қолжетімсіз.',
    en: 'Current metrics are unavailable.',
  },
  'Ошибки относятся ко всему тесту. Сравнение не учитывает тяжесть случаев и мощность. Прогноз потока не измеряет занятость коек. Полноту данных и доступные ресурсы нужно уточнить у специалиста.':
    {
      kk: 'Қателер бүкіл тестке қатысты. Салыстыру жағдайлардың ауырлығы мен қуатты ескермейді. Ағын болжамы төсектердің толуын өлшемейді. Деректердің толықтығы мен қолжетімді ресурстарды маманнан нақтылау қажет.',
      en: 'Errors refer to the full test set. Comparisons do not adjust for case severity or capacity. Flow forecasts do not measure bed occupancy. A specialist should verify data completeness and available resources.',
    },
  'Я проверил период, выбранные стационары, показатели и ограничения.': {
    kk: 'Кезеңді, таңдалған стационарларды, көрсеткіштер мен шектеулерді тексердім.',
    en: 'I have reviewed the period, selected hospitals, metrics and limitations.',
  },
  'Почему различаются наблюдаемые сроки ожидания?': {
    kk: 'Тіркелген күту мерзімдері неге ерекшеленеді?',
    en: 'Why do observed waiting times differ?',
  },
  'Как изменились поток направлений и доступная мощность?': {
    kk: 'Жолдамалар ағыны мен қолжетімді қуат қалай өзгерді?',
    en: 'How have referral flow and available capacity changed?',
  },
  'Каковы причины отказов и полнота регистрации?': {
    kk: 'Бас тарту себептері қандай және тіркеу қаншалықты толық?',
    en: 'What are the reasons for refusals, and how complete are the records?',
  },
  'Код диагноза направления': { kk: 'Жолдамадағы диагноз коды', en: 'Referral diagnosis code' },
  'Профиль койки': { kk: 'Төсек бейіні', en: 'Bed specialty' },
  'Территориальный тип': { kk: 'Аумақ түрі', en: 'Territory type' },
  'Цель направления': { kk: 'Жолдама мақсаты', en: 'Referral purpose' },
  'Источник финансирования': { kk: 'Қаржыландыру көзі', en: 'Funding source' },
  'История этой больницы и профиля': {
    kk: 'Осы аурухана мен бейіннің тарихы',
    en: 'History of this hospital and specialty',
  },
  'История этой больницы · все профили': {
    kk: 'Осы аурухананың тарихы · барлық бейіндер',
    en: 'History of this hospital · all specialties',
  },
  'История профиля · разные больницы': {
    kk: 'Бейін тарихы · әртүрлі ауруханалар',
    en: 'Specialty history · across hospitals',
  },
  'Общая история завершённых госпитализаций': {
    kk: 'Аяқталған жатқызулардың жалпы тарихы',
    en: 'Overall history of completed hospitalizations',
  },
  'CatBoost · параметры направления': {
    kk: 'CatBoost · жолдама параметрлері',
    en: 'CatBoost · referral details',
  },
  'День недели регистрации': { kk: 'Тіркеу аптасының күні', en: 'Registration weekday' },
  'День месяца': { kk: 'Айдың күні', en: 'Day of month' },
  'Месяц регистрации': { kk: 'Тіркеу айы', en: 'Registration month' },
  'День горизонта': { kk: 'Болжам күні', en: 'Forecast horizon day' },
  'День недели прогноза': { kk: 'Болжам аптасының күні', en: 'Forecast weekday' },
  'Последний наблюдённый день': { kk: 'Соңғы тіркелген күн', en: 'Last observed day' },
  'За 6 дней до начала прогноза': {
    kk: 'Болжам басталғанға дейінгі 6-күн',
    en: '6 days before the forecast starts',
  },
  'За 13 дней до начала прогноза': {
    kk: 'Болжам басталғанға дейінгі 13-күн',
    en: '13 days before the forecast starts',
  },
  'Среднее за 7 дней': { kk: '7 күндегі орташа мән', en: '7-day average' },
  'Среднее за 14 дней': { kk: '14 күндегі орташа мән', en: '14-day average' },
  'Среднее за 28 дней': { kk: '28 күндегі орташа мән', en: '28-day average' },
}
