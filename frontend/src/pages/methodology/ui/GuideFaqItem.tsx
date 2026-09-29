import { ChevronDown } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

export function GuideFaqItem({ question, answer }: { question: string; answer: string }) {
  const detailsRef = useRef<HTMLDetailsElement>(null)
  const answerRef = useRef<HTMLDivElement>(null)
  const animationRef = useRef<Animation | null>(null)
  const expandedRef = useRef(false)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => () => animationRef.current?.cancel(), [])

  const toggle = () => {
    const details = detailsRef.current
    const content = answerRef.current
    const summary = details?.querySelector('summary')
    if (!details || !content || !summary) return
    const startHeight = details.getBoundingClientRect().height
    const next = !expandedRef.current
    expandedRef.current = next
    setExpanded(next)
    animationRef.current?.cancel()
    animationRef.current = null

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches || !details.animate) {
      details.open = next
      details.style.overflow = ''
      return
    }

    // Keep native details semantics; closing happens only after the animation.
    details.open = true
    const endHeight =
      summary.getBoundingClientRect().height +
      (next ? content.getBoundingClientRect().height : 0) +
      1
    details.style.overflow = 'hidden'
    const animation = details.animate(
      { height: [`${startHeight}px`, `${endHeight}px`] },
      { duration: 220, easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)' },
    )
    animationRef.current = animation
    animation.onfinish = () => {
      if (animationRef.current !== animation) return
      details.open = next
      details.style.overflow = ''
      animationRef.current = null
    }
  }

  return (
    <details ref={detailsRef} data-expanded={expanded}>
      <summary
        aria-expanded={expanded}
        onClick={(event) => {
          event.preventDefault()
          toggle()
        }}
      >
        {question}
        <ChevronDown size={18} />
      </summary>
      <div ref={answerRef} className="guide-faq-answer">
        <p>{answer}</p>
      </div>
    </details>
  )
}
