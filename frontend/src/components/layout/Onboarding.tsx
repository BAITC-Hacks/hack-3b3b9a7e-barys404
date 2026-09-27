import { ArrowRight, X } from 'lucide-react'
import { useState } from 'react'
import { type User } from '../../api/types'
import { type View } from '../../app/navigation'

export function Onboarding({ user, go }: { user: User; go: (view: View) => void }) {
  const key = `medflow-intro:${user.id}`
  const [visible, setVisible] = useState(() => localStorage.getItem(key) !== 'dismissed')
  if (!visible) return null
  return (
    <section className="onboarding">
      <div>
        <span className="section-kicker">С ЧЕГО НАЧАТЬ</span>
        <h2>
          {user.role === 'hospital_analyst'
            ? 'Ваша больница — уже в кабинете'
            : 'Вся система — в вашем обзоре'}
        </h2>
        <p>Посмотрите динамику направлений, откройте прогноз и узнайте, как читать показатели.</p>
        <button className="text-button" onClick={() => go('data')}>
          Как устроена аналитика <ArrowRight size={15} />
        </button>
      </div>
      <button
        className="icon-button"
        aria-label="Скрыть подсказку"
        onClick={() => {
          localStorage.setItem(key, 'dismissed')
          setVisible(false)
        }}
      >
        <X size={16} />
      </button>
    </section>
  )
}
