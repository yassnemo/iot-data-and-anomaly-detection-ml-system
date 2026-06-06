import { useEffect, useRef } from 'react'

/** Drifting data-point field behind the hero. Pauses off-screen; skipped for reduced motion. */
export default function ParticleField() {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const small = window.innerWidth < 720
    const COUNT = small ? 26 : 56
    const LINK = small ? 100 : 130
    let w = 0, h = 0, raf = 0, running = false
    let pts: { x: number; y: number; vx: number; vy: number; r: number; pulse: number }[] = []

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      w = canvas.clientWidth; h = canvas.clientHeight
      canvas.width = w * dpr; canvas.height = h * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    const seed = () => {
      pts = Array.from({ length: COUNT }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
        r: Math.random() * 1.6 + 0.6, pulse: Math.random() * Math.PI * 2,
      }))
    }
    const frame = () => {
      ctx.clearRect(0, 0, w, h)
      for (let i = 0; i < pts.length; i++) {
        const a = pts[i]
        a.x += a.vx; a.y += a.vy
        if (a.x < 0 || a.x > w) a.vx *= -1
        if (a.y < 0 || a.y > h) a.vy *= -1
        for (let j = i + 1; j < pts.length; j++) {
          const b = pts[j]
          const d = Math.hypot(a.x - b.x, a.y - b.y)
          if (d < LINK) {
            ctx.strokeStyle = `rgba(224, 122, 95, ${(1 - d / LINK) * 0.16})`
            ctx.lineWidth = 1
            ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke()
          }
        }
      }
      const t = performance.now() * 0.002
      pts.forEach((p) => {
        const glow = 0.5 + Math.sin(t + p.pulse) * 0.5
        ctx.beginPath()
        ctx.fillStyle = `rgba(147, 181, 156, ${0.3 + glow * 0.4})`
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill()
      })
      raf = requestAnimationFrame(frame)
    }
    const start = () => { if (!running) { running = true; frame() } }
    const stop = () => { running = false; cancelAnimationFrame(raf) }
    const init = () => { resize(); seed(); stop(); start() }

    init()
    let rt: number
    const onResize = () => { clearTimeout(rt); rt = window.setTimeout(init, 200) }
    window.addEventListener('resize', onResize)
    const io = new IntersectionObserver((e) => e.forEach((x) => (x.isIntersecting ? start() : stop())))
    io.observe(canvas)

    return () => { stop(); window.removeEventListener('resize', onResize); io.disconnect() }
  }, [])

  return <canvas className="hero__canvas" ref={ref} aria-hidden="true" />
}
