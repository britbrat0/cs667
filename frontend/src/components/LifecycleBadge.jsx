import './LifecycleBadge.css'

const STAGE_CONFIG = {
  Emerging: { color: '#27ae60', icon: '\u2197' },     // ↗
  Accelerating: { color: '#2ecc71', icon: '\u2191' },  // ↑
  Peak: { color: '#f39c12', icon: '\u2B50' },           // ⭐ (will render as text)
  Saturation: { color: '#e67e22', icon: '\u2192' },    // →
  Decline: { color: '#e74c3c', icon: '\u2198' },       // ↘
  Dormant: { color: '#95a5a6', icon: '\u23F8' },       // ⏸ (will render as text)
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
