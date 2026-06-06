// Hand-drawn line icons — consistent 24px grid, 1.6 stroke.
const base = {
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export const IcSensor = () => (
  <svg className="ic" {...base}>
    <circle cx="12" cy="12" r="1.8" />
    <path d="M8.4 8.4a5 5 0 0 0 0 7.2M15.6 8.4a5 5 0 0 1 0 7.2" />
    <path d="M5.6 5.6a9 9 0 0 0 0 12.8M18.4 5.6a9 9 0 0 1 0 12.8" />
  </svg>
)

export const IcKafka = () => (
  <svg className="ic" {...base}>
    <rect x="3" y="4.5" width="13" height="4" rx="1" />
    <rect x="8" y="10" width="13" height="4" rx="1" />
    <rect x="3" y="15.5" width="13" height="4" rx="1" />
  </svg>
)

export const IcSpark = () => (
  <svg className="ic" {...base}>
    <rect x="3" y="5" width="10" height="10" rx="1.5" />
    <rect x="11" y="9" width="10" height="10" rx="1.5" />
  </svg>
)

export const IcModel = () => (
  <svg className="ic" {...base}>
    <path d="M6.5 6.8 11 9.4M6.5 11.4 11 9.6M6.5 12.6 11 15.2M6.5 17.2 11 15.4M13 9.5 17.5 12M13 15 17.5 12.5" />
    <circle cx="5" cy="6" r="1.5" />
    <circle cx="5" cy="12" r="1.5" />
    <circle cx="5" cy="18" r="1.5" />
    <circle cx="12" cy="9.5" r="1.5" />
    <circle cx="12" cy="15" r="1.5" />
    <circle cx="19" cy="12" r="1.5" />
  </svg>
)

export const IcAlert = () => (
  <svg className="ic" {...base}>
    <path d="M12 4.5 21 19.5H3z" />
    <path d="M12 10v4.4" />
    <path d="M12 17.4v.01" />
  </svg>
)

export const IcStorage = () => (
  <svg className="ic" {...base}>
    <ellipse cx="12" cy="6" rx="7" ry="3" />
    <path d="M5 6v12c0 1.6 3.1 3 7 3s7-1.4 7-3V6" />
    <path d="M5 12c0 1.6 3.1 3 7 3s7-1.4 7-3" />
  </svg>
)

export const IcMonitor = () => (
  <svg className="ic" {...base}>
    <rect x="3" y="4.5" width="18" height="15" rx="2" />
    <path d="M6.5 13.5 9 10l2.5 4.5L14 8l2 5.5h1.5" />
  </svg>
)

export const IcLogo = () => (
  <svg viewBox="0 0 32 32" width="22" height="22" fill="none">
    <path d="M2 20 L9 20 L12 9 L17 25 L21 14 L24 20 L30 20" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

export const IcGithub = () => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
    <path d="M12 .5C5.7.5.5 5.7.5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.3.8-.6v-2c-3.2.7-3.9-1.4-3.9-1.4-.5-1.3-1.3-1.7-1.3-1.7-1.1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.8 1.3 3.5 1 .1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0C17.3 4.7 18.3 5 18.3 5c.6 1.6.2 2.8.1 3.1.8.8 1.2 1.8 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6 4.6-1.5 7.9-5.8 7.9-10.9C23.5 5.7 18.3.5 12 .5Z" />
  </svg>
)

export const IcArrow = () => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M5 12h14M13 6l6 6-6 6" />
  </svg>
)
