import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Activity, ArrowRight, Building2, Eye, EyeOff, Landmark, LockKeyhole, LogOut, ShieldCheck, TrendingUp, Clock3, ChevronLeft } from 'lucide-react'
import { ApiError, clearPrivateData, get, post, type User } from './api'

export const roleLabel = (role: User['role']) => ({ government_analyst: 'Аналитик госоргана', hospital_analyst: 'Сотрудник больницы', platform_admin: 'Администратор' }[role])

function Brand() {
  return <a className="public-brand" href="#welcome"><span className="brand-mark"><Activity size={25} /></span><span>MedFlow<span>AI</span><small>Госпитальная аналитика</small></span></a>
}

function Welcome() {
  return <div className="welcome-page"><header className="public-header"><Brand /><a href="#login" className="secondary-button welcome-login" aria-label="Войти в кабинет"><span>Войти<span className="welcome-login-detail"> в кабинет</span></span><ArrowRight size={16} /></a></header>
    <main><section className="welcome-hero"><div className="welcome-copy"><span className="public-eyebrow"><span /> ДАННЫЕ ДЛЯ ОБОСНОВАННЫХ РЕШЕНИЙ</span><h1>Видеть поток.<br />Понимать ожидание.</h1><p>Направления, работа стационаров и прогноз входящего потока — в одном рабочем пространстве для больниц и органов здравоохранения.</p><a className="primary-button welcome-cta" href="#login">Войти в рабочий кабинет <ArrowRight size={18} /></a><div className="welcome-access"><ShieldCheck size={17} /><span>Доступ по учётной записи вашей организации</span></div></div>
      <div className="welcome-visual" aria-label="Иллюстрация аналитического кабинета"><div className="visual-top"><span><i /> MedFlow · Обзор</span><span>Иллюстрация</span></div><div className="visual-heading">За цифрами —<br />понятная картина.</div><div className="visual-metrics"><span><Activity size={18} /><small>Направления</small><b>Динамика потока</b></span><span><Clock3 size={18} /><small>Ожидание</small><b>История и оценка</b></span></div><div className="visual-chart"><div><span>Поступление направлений</span><TrendingUp size={17} /></div><svg viewBox="0 0 460 150" role="img" aria-label="Условный график потока, не реальные данные"><defs><linearGradient id="welcome-fill" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#54d9c0" stopOpacity=".3" /><stop offset="1" stopColor="#54d9c0" stopOpacity="0" /></linearGradient></defs><path d="M0 120 L55 105 L110 114 L165 65 L220 82 L275 35 L330 53 L390 20 L460 38 V150 H0Z" fill="url(#welcome-fill)" /><path d="M0 120 L55 105 L110 114 L165 65 L220 82 L275 35 L330 53 L390 20 L460 38" fill="none" stroke="#74e0c9" strokeWidth="3" /></svg><small>История → тенденции → прогноз</small></div><div className="visual-bottom"><ShieldCheck size={16} /> Каждый сотрудник видит разрешённые ему данные</div></div>
    </section><section className="welcome-audiences" aria-label="Для кого платформа"><article><span className="audience-icon"><Building2 size={22} /></span><div><span className="section-kicker">БОЛЬНИЦАМ</span><h2>Своя организация в деталях</h2><p>Динамика направлений, профили госпитализации и прогноз потока вашей больницы.</p></div></article><article><span className="audience-icon"><Landmark size={22} /></span><div><span className="section-kicker">ГОСОРГАНАМ</span><h2>Вся система в одном обзоре</h2><p>Сводные показатели, сравнение стационаров и изменения, требующие внимания.</p></div></article></section>
      <section className="welcome-method"><div><span className="section-kicker">КАК ЧИТАТЬ ПОКАЗАТЕЛИ</span><h2>Понятные данные.<br />Честные ограничения.</h2></div><article><h3>Направления</h3><p>Зарегистрированные обращения в выбранном периоде. Это не число занятых коек.</p></article><article><h3>Ожидание</h3><p>Наблюдаемый срок до госпитализации среди завершённых случаев, а не место в очереди.</p></article><article><h3>Прогноз</h3><p>Оценка по историческим данным. Она помогает анализировать поток, но не назначает дату лечения.</p></article></section>
    </main><footer className="public-footer"><span>MedFlow AI · Демонстрационная платформа</span><span>Исторические данные: январь–март 2025 · Решения принимает специалист</span></footer></div>
}

function Login({ onLogin, notice }: { onLogin: (user: User) => void; notice: string }) {
  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const submit = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError('')
    try { onLogin(await post<User>('/auth/login', { login: login.trim(), password })) }
    catch (reason) { if (!(reason instanceof DOMException && reason.name === 'AbortError')) setError(reason instanceof Error ? reason.message : 'Не удалось войти.') }
    finally { setBusy(false) }
  }
  return <div className="login-page"><div className="login-story"><Brand /><div><span className="public-eyebrow">ВАШЕ РАБОЧЕЕ ПРОСТРАНСТВО</span><h1>Данные вашей организации.<br />Ваши решения.</h1><p>Войдите, чтобы открыть аналитику и прогнозы. Платформа автоматически загрузит кабинет с правами вашей учётной записи.</p></div><span className="login-security"><ShieldCheck size={19} /> Доступ к данным ограничен ролью и организацией</span></div><main className="login-main"><a className="back-link" href="#welcome"><ChevronLeft size={16} /> О платформе</a><div className="login-form-card"><span className="login-lock"><LockKeyhole size={23} /></span><h2>Вход в кабинет</h2><p>Используйте учётную запись, выданную администратором.</p>{notice && <div className="auth-notice" role="status">{notice}</div>}<form onSubmit={submit}><label>Логин<input autoComplete="username" autoFocus required maxLength={120} value={login} onChange={event => setLogin(event.target.value)} placeholder="Ваш логин" /></label><label>Пароль<span className="password-input"><input type={show ? 'text' : 'password'} autoComplete="current-password" required maxLength={128} value={password} onChange={event => setPassword(event.target.value)} placeholder="Введите пароль" /><button type="button" onClick={() => setShow(!show)} aria-label={show ? 'Скрыть пароль' : 'Показать пароль'}>{show ? <EyeOff size={18} /> : <Eye size={18} />}</button></span></label>{error && <div className="message message-error" role="alert">{error}</div>}<button className="primary-button" disabled={busy}>{busy ? 'Входим…' : 'Войти в кабинет'}<ArrowRight size={17} /></button></form><div className="login-help"><strong>Нет доступа или забыли пароль?</strong><p>Обратитесь к администратору платформы. Он создаст учётную запись или поможет восстановить доступ.</p></div></div><small className="login-caption">MedFlow AI · Аналитика на исторических данных</small></main></div>
}

function ChangePassword({ onDone, onLogout }: { onDone: () => void; onLogout: () => Promise<void> }) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  return <main className="auth-state"><div className="login-form-card"><LockKeyhole size={25} /><h1>Установите свой пароль</h1><p>Вы вошли с временным паролем. Перед началом работы замените его на личный — от 12 до 128 символов.</p><form onSubmit={async event => { event.preventDefault(); setBusy(true); setError(''); try { await post('/auth/change-password', { current_password: current, new_password: next }); onDone() } catch (reason) { setError(reason instanceof Error ? reason.message : 'Ошибка') } finally { setBusy(false) } }}><label>Временный пароль<input type="password" autoComplete="current-password" value={current} onChange={e => setCurrent(e.target.value)} required /></label><label>Новый пароль<input type="password" autoComplete="new-password" minLength={12} maxLength={128} value={next} onChange={e => setNext(e.target.value)} required /></label>{error && <p className="message message-error" role="alert">{error}</p>}<button className="primary-button" disabled={busy}>Сохранить пароль</button></form><button className="text-button" onClick={() => { void onLogout().catch(reason => setError(reason.message)) }}>Выйти</button></div></main>
}

export function AuthGate({ children }: { children: (user: User, logout: () => Promise<void>) => ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [checking, setChecking] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [hash, setHash] = useState(window.location.hash)
  const channel = useRef<BroadcastChannel | null>(null)
  const version = useRef(0)
  const reset = (message: string) => {
    version.current++; clearPrivateData(); setUser(null); setChecking(false); setError(''); setNotice(message)
  }
  const check = async () => {
    const attempt = ++version.current
    try { const account = await get<User>('/auth/me'); if (attempt === version.current) { setUser(account); setError('') } }
    catch (reason) {
      if (attempt !== version.current || (reason instanceof DOMException && reason.name === 'AbortError')) return
      if (reason instanceof ApiError && reason.status === 401) reset('')
      else setError('Не удалось связаться с сервером. Проверьте подключение и повторите попытку.')
    } finally { if (attempt === version.current) setChecking(false) }
  }
  useEffect(() => {
    void check()
    const route = () => setHash(window.location.hash)
    const expired = () => { reset('Сессия завершена. Войдите снова, чтобы продолжить.'); window.location.hash = 'login' }
    const tab = new BroadcastChannel('medflow-session'); channel.current = tab
    tab.onmessage = () => { reset('Учётная запись изменена в другой вкладке.'); setChecking(true); void check() }
    const restored = (event: PageTransitionEvent) => { if (event.persisted) { reset(''); setChecking(true); void check() } }
    window.addEventListener('hashchange', route); window.addEventListener('session-expired', expired)
    window.addEventListener('pageshow', restored)
    return () => { version.current++; clearPrivateData(); tab.close(); window.removeEventListener('hashchange', route); window.removeEventListener('session-expired', expired); window.removeEventListener('pageshow', restored) }
  }, [])
  useEffect(() => {
    if (!user) return
    let lastActivity = Date.now()
    const activity = () => {
      if (Date.now() - lastActivity < 60000) return
      lastActivity = Date.now()
      void post('/auth/activity', {}).catch(() => {})
    }
    const verify = async () => {
      try {
        const latest = await get<User>('/auth/me')
        if (latest.id !== user.id || latest.role !== user.role || latest.hospital_id !== user.hospital_id) { reset(''); setChecking(true); void check() }
      } catch (reason) { if (reason instanceof ApiError && reason.status === 401) { reset('Сессия завершена. Войдите снова.'); window.location.hash = 'login' } }
    }
    const interval = window.setInterval(verify, 60000)
    const focus = () => { void verify() }
    window.addEventListener('pointerdown', activity); window.addEventListener('keydown', activity); window.addEventListener('focus', focus)
    return () => { window.clearInterval(interval); window.removeEventListener('pointerdown', activity); window.removeEventListener('keydown', activity); window.removeEventListener('focus', focus) }
  }, [user])
  const logout = async () => {
    await post('/auth/logout', {})
    reset('Вы вышли из аккаунта.'); channel.current?.postMessage('changed'); window.location.hash = 'login'
  }
  if (checking) return <main className="auth-state"><div className="spinner" /><p>Проверяем сеанс…</p></main>
  if (error && !user) return <main className="auth-state"><p role="alert">{error}</p><button className="primary-button" onClick={() => { setChecking(true); void check() }}>Повторить</button></main>
  if (user?.must_change_password) return <ChangePassword onLogout={logout} onDone={() => { reset('Пароль изменён. Войдите с новым паролем.'); channel.current?.postMessage('changed'); window.location.hash = 'login' }} />
  if (user) return <div key={user.id}>{children(user, logout)}</div>
  const showLogin = hash && hash !== '#welcome'
  return showLogin ? <Login notice={notice} onLogin={account => { clearPrivateData(); setUser(account); setNotice(''); channel.current?.postMessage('changed'); if (['#login', '#welcome', ''].includes(window.location.hash)) window.location.hash = 'overview' }} /> : <Welcome />
}

export function UserMenu({ user, logout }: { user: User; logout: () => Promise<void> }) {
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  return <div className="user-menu"><div><strong>{user.display_name}</strong><small>{roleLabel(user.role)}</small></div><button className="icon-button" disabled={busy} title="Выйти" aria-label="Выйти из аккаунта" onClick={async () => { setBusy(true); setError(''); try { await logout() } catch { setError('Не удалось выйти. Повторите.'); setBusy(false) } }}><LogOut size={17} /></button>{error && <span role="alert">{error}</span>}</div>
}
