// Known API status messages only. Do not rewrite arbitrary source-data values.
export const serverAliases: Readonly<Record<string, string>> = {
  'Failed to fetch': 'Не удалось подключиться к серверу. Проверьте соединение.',
  'NetworkError when attempting to fetch resource.':
    'Не удалось подключиться к серверу. Проверьте соединение.',
  'Load failed': 'Не удалось подключиться к серверу. Проверьте соединение.',
  'Model has not been trained. Run python -m ml.train_waiting_model.':
    'Модель ещё не обучена. Обратитесь к администратору.',
  'Data-quality report is missing; rebuild data and train the model.':
    'Отчёт о качестве данных отсутствует. Требуется подготовка данных и обучение модели.',
  'Waiting model protocol changed. Retrain the model.':
    'Протокол модели ожидания изменился. Требуется переобучение.',
  'Data processing is incomplete. Finish preprocessing and retrain the model.':
    'Обработка данных не завершена. Завершите подготовку и переобучите модель.',
  'Source or processed data changed. Retrain the model.':
    'Данные изменились. Требуется переобучение модели.',
  'Model ready.': 'Модель готова.',
  'Forecast artifacts or source data changed. Refresh data and retrain the forecast.':
    'Данные или файлы прогноза изменились. Обновите данные и переобучите модель.',
  'No 7-day referral-load model has been trained.': 'Модель потока на 7 дней ещё не обучена.',
  'Forecast model ready.': 'Модель прогноза готова.',
}
