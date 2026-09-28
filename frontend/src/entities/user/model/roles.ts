import { type User } from '../../../shared/api/types'

export const roleLabel = (role: User['role']) =>
  ({
    government_analyst: 'Аналитик госоргана',
    hospital_analyst: 'Сотрудник больницы',
    platform_admin: 'Администратор',
  })[role]
