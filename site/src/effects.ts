import { useEffect, useRef, useState } from 'react'

/**
 * Ports the imperative behaviour of the original site into one hook:
 * scroll progress, sticky nav, scroll-reveal, count-up, scrollspy,
 * and the architecture diagram's sequential light-up.
 */
export function useSiteBehavior() {
  const [stuck, setStuck] = useState(false)
  const [active, setActive] = useState('')
  const progressRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const all = (s: string) => Array.from(document.querySelectorAll(s)) as HTMLElement[]
    const observers: IntersectionObserver[] = []
    let interval: number | undefined

    // scroll progress + sticky nav
    let stuckState = false
    const onScroll = () => {
      const y = window.scrollY || window.pageYOffset
      const h = document.documentElement.scrollHeight - window.innerHeight
      if (progressRef.current) progressRef.current.style.width = `${h > 0 ? (y / h) * 100 : 0}%`
      const s = y > 24
      if (s !== stuckState) { stuckState = s; setStuck(s) }
    }
    window.addEventListener('scroll', onScroll, { passive: true })
    onScroll()

    // scroll reveal
    const revealEls = all('.reveal')
    if (reduce) {
      revealEls.forEach((e) => e.classList.add('is-visible'))
    } else {
      const ro = new IntersectionObserver(
        (entries) => entries.forEach((e) => {
          if (e.isIntersecting) { e.target.classList.add('is-visible'); ro.unobserve(e.target) }
        }),
        { threshold: 0.12, rootMargin: '0px 0px -8% 0px' },
      )
      revealEls.forEach((e) => ro.observe(e))
      observers.push(ro)
    }

    // timeline markers
    const tlo = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && e.target.classList.add('is-visible')),
      { threshold: 0.4 },
    )
    all('.timeline__item').forEach((e) => tlo.observe(e))
    observers.push(tlo)

    // count-up
    const fmt = (n: number, float: boolean) => (float ? n.toFixed(1) : Math.round(n).toLocaleString('en-US'))
    const animateCount = (el: HTMLElement) => {
      const target = parseFloat(el.dataset.target || '0')
      const float = !Number.isInteger(target)
      const start = performance.now()
      const dur = 1500
      const tick = (now: number) => {
        const p = Math.min((now - start) / dur, 1)
        const eased = p === 1 ? 1 : 1 - Math.pow(2, -10 * p)
        el.textContent = fmt(target * eased, float)
        if (p < 1) requestAnimationFrame(tick)
        else el.textContent = fmt(target, float)
      }
      requestAnimationFrame(tick)
    }
    const counts = all('.count')
    if (reduce) {
      counts.forEach((el) => {
        const t = parseFloat(el.dataset.target || '0')
        el.textContent = Number.isInteger(t) ? t.toLocaleString('en-US') : t.toFixed(1)
      })
    } else {
      const co = new IntersectionObserver(
        (entries) => entries.forEach((e) => {
          if (e.isIntersecting) { animateCount(e.target as HTMLElement); co.unobserve(e.target) }
        }),
        { threshold: 0.6 },
      )
      counts.forEach((el) => co.observe(el))
      observers.push(co)
    }

    // scrollspy
    const spy = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) setActive(e.target.id) }),
      { rootMargin: '-45% 0px -50% 0px' },
    )
    all('.app section[id]').forEach((s) => spy.observe(s))
    observers.push(spy)

    // architecture diagram: sequential light-up
    if (!reduce) {
      const diagram = document.querySelector('#diagram')
      if (diagram) {
        const nodes = Array.from(diagram.querySelectorAll('.node')) as HTMLElement[]
        const dio = new IntersectionObserver(
          (entries) => entries.forEach((e) => {
            if (e.isIntersecting && interval === undefined && nodes.length) {
              let i = 0
              const loop = () => {
                nodes.forEach((n) => n.classList.remove('is-lit'))
                nodes[i].classList.add('is-lit')
                i = (i + 1) % nodes.length
              }
              loop()
              interval = window.setInterval(loop, 900)
            }
          }),
          { threshold: 0.3 },
        )
        dio.observe(diagram)
        observers.push(dio)
      }
    }

    return () => {
      window.removeEventListener('scroll', onScroll)
      observers.forEach((o) => o.disconnect())
      if (interval) clearInterval(interval)
    }
  }, [])

  return { stuck, active, progressRef }
}
