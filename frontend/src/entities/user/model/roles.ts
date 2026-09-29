import { t } from '../../../shared/lib/i18n'
import { type User } from '../../../shared/api/types'

export const roleLabel = (role: User['role']) =>
  ({
    government_analyst: t('Аналитик госоргана'),
    hospital_analyst: t('Сотрудник больницы'),
    platform_admin: t('Администратор'),
  })[role]
