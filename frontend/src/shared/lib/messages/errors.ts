export const errorMessages: Record<string, { kk: string; en: string }> = {
  'Сервис временно недоступен. Повторите попытку позже.': {
    kk: 'Қызмет уақытша қолжетімсіз. Кейінірек қайталап көріңіз.',
    en: 'The service is temporarily unavailable. Please try again later.',
  },
  'Не удалось подключиться к серверу. Проверьте соединение.': {
    kk: 'Серверге қосылу мүмкін болмады. Байланысты тексеріңіз.',
    en: 'Could not connect to the server. Check your connection.',
  },
  'Модель ещё не обучена. Обратитесь к администратору.': {
    kk: 'Модель әлі оқытылмаған. Әкімшіге хабарласыңыз.',
    en: 'The model has not been trained yet. Contact your administrator.',
  },
  'Отчёт о качестве данных отсутствует. Требуется подготовка данных и обучение модели.': {
    kk: 'Деректер сапасының есебі жоқ. Деректерді дайындап, модельді оқыту қажет.',
    en: 'The data-quality report is missing. Prepare the data and train the model.',
  },
  'Протокол модели ожидания изменился. Требуется переобучение.': {
    kk: 'Күту уақытын бағалау моделінің хаттамасы өзгерген. Қайта оқыту қажет.',
    en: 'The waiting-time model protocol has changed. Retraining is required.',
  },
  'Обработка данных не завершена. Завершите подготовку и переобучите модель.': {
    kk: 'Деректерді өңдеу аяқталмаған. Дайындауды аяқтап, модельді қайта оқытыңыз.',
    en: 'Data processing is incomplete. Finish preparation and retrain the model.',
  },
  'Данные изменились. Требуется переобучение модели.': {
    kk: 'Деректер өзгерген. Модельді қайта оқыту қажет.',
    en: 'The data has changed. The model needs retraining.',
  },
  'Модель готова.': { kk: 'Модель дайын.', en: 'The model is ready.' },
  'Данные или файлы прогноза изменились. Обновите данные и переобучите модель.': {
    kk: 'Деректер немесе болжам файлдары өзгерген. Деректерді жаңартып, модельді қайта оқытыңыз.',
    en: 'The data or forecast files have changed. Update the data and retrain the model.',
  },
  'Модель потока на 7 дней ещё не обучена.': {
    kk: '7 күндік жолдамалар ағынының моделі әлі оқытылмаған.',
    en: 'The 7-day referral model has not been trained yet.',
  },
  'Модель прогноза готова.': { kk: 'Болжам моделі дайын.', en: 'The forecast model is ready.' },
  'Источник запроса не разрешён.': {
    kk: 'Сұрау көзіне рұқсат берілмеген.',
    en: 'This request origin is not allowed.',
  },
  'Обновите страницу и повторите действие.': {
    kk: 'Бетті жаңартып, әрекетті қайталаңыз.',
    en: 'Refresh the page and try again.',
  },
  'Войдите в рабочий кабинет.': {
    kk: 'Жұмыс кабинетіне кіріңіз.',
    en: 'Sign in to your workspace.',
  },
  'Сначала смените временный пароль.': {
    kk: 'Алдымен уақытша құпиясөзді өзгертіңіз.',
    en: 'Change your temporary password first.',
  },
  'Этот раздел недоступен для вашей роли.': {
    kk: 'Бұл бөлім сіздің рөліңізге қолжетімсіз.',
    en: 'This section is not available for your role.',
  },
  'Доступ к организации ещё не настроен. Обратитесь к администратору.': {
    kk: 'Ұйымға қолжетімділік әлі бапталмаған. Әкімшіге хабарласыңыз.',
    en: 'Organisation access has not been set up. Contact your administrator.',
  },
  'Доступ к организации ещё не настроен.': {
    kk: 'Ұйымға қолжетімділік әлі бапталмаған.',
    en: 'Organisation access has not been set up.',
  },
  'Стационар недоступен.': { kk: 'Стационар қолжетімсіз.', en: 'This hospital is unavailable.' },
  'Нет доступа к аналитике.': {
    kk: 'Аналитикаға қолжетімділік жоқ.',
    en: 'You do not have access to analytics.',
  },
  'Выберите стационар.': { kk: 'Стационарды таңдаңыз.', en: 'Select a hospital.' },
  'Слишком много запросов. Повторите через минуту.': {
    kk: 'Сұраулар тым көп. Бір минуттан кейін қайталаңыз.',
    en: 'Too many requests. Try again in a minute.',
  },
  'Слишком много попыток входа. Повторите через 15 минут.': {
    kk: 'Кіру әрекеттері тым көп. 15 минуттан кейін қайталаңыз.',
    en: 'Too many sign-in attempts. Try again in 15 minutes.',
  },
  'Неверный логин или пароль.': {
    kk: 'Логин немесе құпиясөз қате.',
    en: 'Incorrect username or password.',
  },
  'Слишком много попыток. Повторите через 15 минут.': {
    kk: 'Әрекеттер тым көп. 15 минуттан кейін қайталаңыз.',
    en: 'Too many attempts. Try again in 15 minutes.',
  },
  'Текущий пароль указан неверно.': {
    kk: 'Қазіргі құпиясөз қате көрсетілген.',
    en: 'The current password is incorrect.',
  },
  'Пароль должен содержать от 12 до 128 символов.': {
    kk: 'Құпиясөз 12–128 таңбадан тұруы керек.',
    en: 'The password must contain 12–128 characters.',
  },
  'Нет доступа к управлению аккаунтами.': {
    kk: 'Тіркелгілерді басқаруға рұқсат жоқ.',
    en: 'You do not have permission to manage accounts.',
  },
  'Аккаунт уже удалён или не найден. Обновите список.': {
    kk: 'Тіркелгі жойылған немесе табылмады. Тізімді жаңартыңыз.',
    en: 'The account was deleted or could not be found. Refresh the list.',
  },
  'Логин аккаунта изменился. Обновите список перед удалением.': {
    kk: 'Тіркелгінің логині өзгерген. Жою алдында тізімді жаңартыңыз.',
    en: 'The account username has changed. Refresh the list before deleting it.',
  },
  'Нельзя заблокировать или удалить свой аккаунт.': {
    kk: 'Өз тіркелгіңізді бұғаттауға немесе жоюға болмайды.',
    en: 'You cannot block or delete your own account.',
  },
  'Нельзя заблокировать или удалить последнего администратора.': {
    kk: 'Соңғы әкімшіні бұғаттауға немесе жоюға болмайды.',
    en: 'You cannot block or delete the last administrator.',
  },
  'Проверьте логин и роль.': {
    kk: 'Логин мен рөлді тексеріңіз.',
    en: 'Check the username and role.',
  },
  'Сотруднику больницы необходимо назначить организацию.': {
    kk: 'Аурухана қызметкеріне ұйым тағайындау қажет.',
    en: 'Assign an organisation to the hospital staff member.',
  },
  'Привязка к больнице используется только для сотрудника больницы.': {
    kk: 'Ауруханаға байланыстыру тек аурухана қызметкері үшін қолданылады.',
    en: 'Hospital assignment only applies to hospital staff.',
  },
  'Организация не найдена.': { kk: 'Ұйым табылмады.', en: 'Organisation not found.' },
  'Пользователь не найден.': { kk: 'Пайдаланушы табылмады.', en: 'User not found.' },
  'Неизвестная роль.': { kk: 'Белгісіз рөл.', en: 'Unknown role.' },
  'Назначьте действующую больницу.': {
    kk: 'Қолданыстағы аурухананы тағайындаңыз.',
    en: 'Assign an available hospital.',
  },
  'Нельзя отключить последнего администратора.': {
    kk: 'Соңғы әкімшіні өшіруге болмайды.',
    en: 'You cannot disable the last administrator.',
  },
  'Подготовленные данные не найдены. Запустите подготовку данных.': {
    kk: 'Дайындалған деректер табылмады. Деректерді дайындау үшін әкімшіге хабарласыңыз.',
    en: 'Prepared data was not found. Ask your administrator to prepare the data.',
  },
  'Подготовка данных не завершена.': {
    kk: 'Деректерді дайындау аяқталмаған.',
    en: 'Data preparation has not finished.',
  },
  'Исходные CSV изменились. Обновите данные и модели через python -m scripts.bootstrap.': {
    kk: 'Бастапқы деректер өзгерген. Әкімшіден деректер мен модельдерді жаңартуды сұраңыз.',
    en: 'The source data has changed. Ask your administrator to update the data and models.',
  },
  'Начало периода должно быть раньше конца.': {
    kk: 'Кезеңнің басталуы аяқталуынан бұрын болуы керек.',
    en: 'The start date must be before the end date.',
  },
  'Название стационара слишком длинное.': {
    kk: 'Стационар атауы тым ұзын.',
    en: 'The hospital name is too long.',
  },
  'Прогноз потока недоступен: данные или модель изменились.': {
    kk: 'Жолдамалар ағынының болжамы қолжетімсіз: деректер немесе модель өзгерген.',
    en: 'The referral forecast is unavailable because the data or model has changed.',
  },
  'Для этого стационара недостаточно истории прогноза.': {
    kk: 'Бұл стационар бойынша болжам жасауға тарихи деректер жеткіліксіз.',
    en: 'There is not enough history to forecast for this hospital.',
  },
  'Модель ожидания недоступна.': {
    kk: 'Күту уақытын бағалау моделі қолжетімсіз.',
    en: 'The waiting-time model is unavailable.',
  },
  'Для выбранной больницы и профиля недостаточно данных для оценки.': {
    kk: 'Таңдалған аурухана мен бейін бойынша бағалауға деректер жеткіліксіз.',
    en: 'There is not enough data to estimate for this hospital and specialty.',
  },
  'Для этого профиля нет завершённых случаев в выбранном стационаре.': {
    kk: 'Таңдалған стационарда бұл бейін бойынша аяқталған жағдайлар жоқ.',
    en: 'There are no completed cases for this specialty at the selected hospital.',
  },
  'Дата должна находиться в периоде исторической проверки модели.': {
    kk: 'Күн модельдің тарихи тексеру кезеңіне сәйкес келуі керек.',
    en: 'The date must fall within the model’s historical test period.',
  },
  'Выберите разные стационары.': {
    kk: 'Әртүрлі стационарларды таңдаңыз.',
    en: 'Select different hospitals.',
  },
  'В выбранном периоде не для всех стационаров достаточно направлений. Уточните выбор.': {
    kk: 'Таңдалған кезеңде кейбір стационарларда жолдамалар жеткіліксіз. Таңдауды өзгертіңіз.',
    en: 'Some hospitals have too few referrals in this period. Adjust your selection.',
  },
  'Сначала проверьте сводку и подтвердите просмотр.': {
    kk: 'Алдымен жиынтықты тексеріп, қарап шыққаныңызды растаңыз.',
    en: 'Review the summary and confirm that you have checked it first.',
  },
  'Контекст сводки изменился. Загрузите новый просмотр и подтвердите его.': {
    kk: 'Жиынтық деректері өзгерген. Жаңа нұсқаны жүктеп, қайта растаңыз.',
    en: 'The summary context has changed. Load a new preview and review it again.',
  },
  'Сводка не помещается на страницу. Уменьшите число стационаров.': {
    kk: 'Жиынтық бетке сыймайды. Стационарлар санын азайтыңыз.',
    en: 'The summary does not fit on the page. Select fewer hospitals.',
  },
}
