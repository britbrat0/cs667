import './LifecycleBadge.css'

const STAGE_CONFIG = {
  Emerging: { color: '#6a9ab8', icon: '\u2197' },      // dusty blue ↗
  Accelerating: { color: '#c9607a', icon: '\u2191' },  // dusty rose ↑
  Peak: { color: '#cc3333', icon: '\u2B50' },           // red ⭐
  Saturation: { color: '#b07070', icon: '\u2192' },    // muted rose →
  Decline: { color: '#8a8a8a', icon: '\u2198' },       // grey ↘
  Dormant: { color: '#b5b5b5', icon: '\u23F8' },       // light grey ⏸
}

export default function LifecycleBadge({ stage, size = 'normal' }) {
  const config = STAGE_CONFIG[stage] || { color: '#95a5a6', icon: '?' }

  return (
    <span
      className={`lifecycle-badge lifecycle-badge--${size}`}
      style={{ backgroundColor: config.color }}
    >
      <span className="lifecycle-icon">{config.icon}</span>
      {stage}
    </span>
  )
}
