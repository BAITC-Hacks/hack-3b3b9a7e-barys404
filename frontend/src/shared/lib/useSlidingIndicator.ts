import { useCallback, useEffect, useLayoutEffect, useRef } from 'react'

export function useSlidingIndicator<T extends HTMLElement>(value: string) {
  const trackRef = useRef<T>(null)
  const indicatorRef = useRef<HTMLSpanElement>(null)
  const animation = useRef<Animation | null>(null)
  const initialized = useRef(false)
  const place = useCallback((animate = false) => {
    const track = trackRef.current,
      indicator = indicatorRef.current
    const active = track?.querySelector<HTMLElement>(
      'button[aria-selected="true"],button[aria-pressed="true"]',
    )
    if (!track || !indicator || !active || !active.offsetWidth) return
    // Read the live presentation before cancellation so rapid clicks do not jump.
    const current = indicator.getBoundingClientRect(),
      origin = track.getBoundingClientRect()
    animation.current?.cancel()
    const target = `translate(${active.offsetLeft}px, ${active.offsetTop}px)`
    indicator.style.width = `${active.offsetWidth}px`
    indicator.style.height = `${active.offsetHeight}px`
    indicator.style.transform = target
    indicator.style.opacity = '1'
    if (
      animate &&
      initialized.current &&
      !window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      animation.current = indicator.animate(
        [
          {
            transform: `translate(${current.left - origin.left - track.clientLeft}px, ${current.top - origin.top - track.clientTop}px) scaleX(${current.width / active.offsetWidth})`,
          },
          { transform: target },
        ],
        { duration: 420, easing: 'cubic-bezier(0.22, 1, 0.36, 1)' },
      )
    }
    initialized.current = true
  }, [])
  useLayoutEffect(() => {
    place(true)
  }, [value, place])
  useEffect(() => {
    const track = trackRef.current
    if (!track) return
    const resize = new ResizeObserver(() => place())
    resize.observe(track)
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)')
    const changed = () => place()
    preference.addEventListener('change', changed)
    return () => {
      resize.disconnect()
      preference.removeEventListener('change', changed)
      animation.current?.cancel()
    }
  }, [place])
  return { trackRef, indicatorRef }
}
