export const message = (error: unknown) =>
  error instanceof Error ? error.message : 'Не удалось выполнить действие.'
