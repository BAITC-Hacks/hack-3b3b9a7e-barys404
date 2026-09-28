import { useCallback } from 'react'

type Entrance = 'fade' | 'lift' | 'slide' | 'draw' | 'grow'

// Shared presentation only: no timers, layout measurements or data changes.
export function animateEntrance(element: Element, variant: Entrance = 'lift', delay = 0) {
  const preference = window.matchMedia('(prefers-reduced-motion: reduce)')
  if (preference.matches || typeof element.animate !== 'function') return () => {}
  const frames: Record<Entrance, Keyframe[]> = {
    fade: [{ opacity: 0.2 }, { opacity: 1 }],
    lift: [
      { opacity: 0, transform: 'translateY(18px)' },
      { opacity: 1, transform: 'translateY(0)' },
    ],
    slide: [
      { opacity: 0.2, transform: 'translateX(18px)' },
      { opacity: 1, transform: 'translateX(0)' },
    ],
    draw: [{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }],
    grow: [{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }],
  }
  const durations: Record<Entrance, number> = {
    fade: 340,
    lift: 560,
    slide: 420,
    draw: 850,
    grow: 700,
  }
  const animation = element.animate(frames[variant], {
    duration: durations[variant],
    delay,
    fill: 'backwards',
    easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)',
  })
  const stop = () => {
    if (preference.matches) animation.cancel()
  }
  const detach = () => preference.removeEventListener('change', stop)
  preference.addEventListener('change', stop)
  animation.addEventListener('finish', detach, { once: true })
  animation.addEventListener('cancel', detach, { once: true })
  return () => {
    animation.cancel()
    detach()
  }
}

// React 19 runs the returned cleanup on unmount or a new trigger: rapid
// navigation cancels the previous effect without remounting/resetting a form.
export function useEntrance<T extends Element>(trigger?: unknown, variant: Entrance = 'lift') {
  return useCallback(
    (element: T | null) => (element ? animateEntrance(element, variant) : undefined),
    [trigger, variant],
  )
}

// Reveal once when a group enters the viewport, not before the user scrolls to it.
export function useStaggeredEntrance<T extends HTMLElement>(
  trigger?: unknown,
  variant: Entrance = 'lift',
  selector = ':scope > *',
) {
  return useCallback(
    (element: T | null) => {
      if (!element) return
      const cleanups: (() => void)[] = []
      let started = false
      const start = () => {
        if (started) return
        started = true
        element.querySelectorAll(selector).forEach((child, index) => {
          cleanups.push(animateEntrance(child, variant, Math.min(index, 4) * 90))
        })
      }
      let observer: IntersectionObserver | undefined
      if (typeof IntersectionObserver === 'function') {
        observer = new IntersectionObserver(
          (entries) => {
            if (entries.some((entry) => entry.isIntersecting)) {
              observer?.disconnect()
              start()
            }
          },
          { threshold: 0.1 },
        )
        observer.observe(element)
      } else start()
      return () => {
        observer?.disconnect()
        cleanups.forEach((cleanup) => cleanup())
      }
    },
    [trigger, variant, selector],
  )
}
