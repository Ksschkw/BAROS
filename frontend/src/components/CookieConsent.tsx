import { useState, useEffect } from 'react'

const CONSENT_KEY = 'baros_cookie_consent'

export function useCookieConsent() {
  const [hasConsent, setHasConsent] = useState<boolean>(() => {
    return localStorage.getItem(CONSENT_KEY) === 'granted'
  })

  const grantConsent = () => {
    localStorage.setItem(CONSENT_KEY, 'granted')
    setHasConsent(true)
  }

  return { hasConsent, grantConsent }
}

export function CookieConsentBanner() {
  const { hasConsent, grantConsent } = useCookieConsent()
  const [visible, setVisible] = useState(false)

  // Slight delay so it doesn't pop immediately on page load
  useEffect(() => {
    if (!hasConsent) {
      const t = setTimeout(() => setVisible(true), 800)
      return () => clearTimeout(t)
    }
  }, [hasConsent])

  if (hasConsent || !visible) return null

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        padding: '16px 24px',
        background: 'rgba(0,0,0,0.92)',
        backdropFilter: 'blur(12px)',
        borderTop: '1px solid rgba(255,255,255,0.12)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        color: '#fff',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '260px' }}>
          <p style={{ margin: 0, fontSize: '14px', lineHeight: '1.5', color: '#e5e7eb' }}>
            <span style={{ fontWeight: 600, color: '#fff' }}>BAROS uses essential cookies</span> to keep you
            signed in. These are required for authentication only — we do not use tracking cookies.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexShrink: 0, alignItems: 'center' }}>
          <a
            href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: '13px',
              color: '#9ca3af',
              textDecoration: 'underline',
              padding: '8px 12px',
            }}
          >
            Learn More
          </a>
          <button
            onClick={grantConsent}
            style={{
              background: '#fff',
              color: '#000',
              border: 'none',
              borderRadius: '8px',
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'opacity 0.15s',
            }}
            onMouseOver={(e) => ((e.target as HTMLButtonElement).style.opacity = '0.9')}
            onMouseOut={(e) => ((e.target as HTMLButtonElement).style.opacity = '1')}
          >
            Allow Essential Cookies
          </button>
        </div>
      </div>
    </div>
  )
}
