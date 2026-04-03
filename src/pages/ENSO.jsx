jsximport { useState } from 'react'

// ── Add future cities here ─────────────────────────────
// Each entry needs a label and either one or two chart URLs.
// If a city only has one chart, omit chart2.
const CITIES = [
  {
    id:     'isp',
    label:  'Islip, NY',
    chart1: 'https://josht3113.github.io/ENSO-Charts/',
    chart2: 'https://josht3113.github.io/ENSO-Charts/', // update if chart 2 is a different URL
  },
  // { id: 'jfk', label: 'JFK, NY', chart1: '...', chart2: '...' },
]

export default function ENSO() {
  const [active, setActive] = useState(CITIES[0].id)
  const city = CITIES.find(c => c.id === active)

  return (
    <div className="page-container">

      {/* ── Hero ── */}
      <div className="page-hero">
        <p className="page-eyebrow">El Niño · La Niña · Neutral</p>
        <h1 className="page-title">ENSO Influence</h1>
        <p className="page-subtitle">
          How El Niño–Southern Oscillation patterns shift seasonal
          temperature and precipitation across your region.
        </p>
      </div>

      {/* ── City selector ── */}
      {CITIES.length > 1 && (
        <div style={styles.tabs}>
          {CITIES.map(c => (
            <button
              key={c.id}
              onClick={() => setActive(c.id)}
              style={{
                ...styles.tab,
                ...(active === c.id ? styles.tabActive : {}),
              }}
            >
              {c.label}
            </button>
          ))}
        </div>
      )}

      {/* ── Charts ── */}
      <div style={styles.charts}>
        <iframe
          src={city.chart1}
          title={`${city.label} ENSO Chart 1`}
          style={styles.frame}
          loading="lazy"
        />
        {city.chart2 && (
          <iframe
            src={city.chart2}
            title={`${city.label} ENSO Chart 2`}
            style={styles.frame}
            loading="lazy"
          />
        )}
      </div>

    </div>
  )
}

const styles = {
  tabs: {
    display:      'flex',
    gap:          '8px',
    marginBottom: '1.5rem',
    flexWrap:     'wrap',
  },
  tab: {
    fontFamily:      'var(--font-mono)',
    fontSize:        '11px',
    fontWeight:      500,
    letterSpacing:   '0.08em',
    textTransform:   'uppercase',
    padding:         '6px 14px',
    borderRadius:    'var(--radius-sm)',
    border:          '0.5px solid var(--color-border)',
    background:      'var(--color-surface)',
    color:           'var(--color-text-secondary)',
    cursor:          'pointer',
    transition:      'all 0.15s',
  },
  tabActive: {
    background:   'rgba(127, 119, 221, 0.12)',
    border:       '0.5px solid rgba(127, 119, 221, 0.4)',
    color:        'var(--accent-enso)',
  },
  charts: {
    display:       'flex',
    flexDirection: 'column',
    gap:           '1.5rem',
    paddingBottom: '3rem',
  },
  frame: {
    width:        '100%',
    height:       '500px',
    border:       '0.5px solid var(--color-border)',
    borderRadius: 'var(--radius-md)',
    background:   'var(--color-surface)',
    display:      'block',
  },
}
