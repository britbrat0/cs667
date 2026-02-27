import InfoTooltip from './Charts/InfoTooltip'
import './TrendCycleIndicator.css'

const STAGES = [
  { key: 'emerging',     label: 'Emerging',     x: 0.10 },
  { key: 'accelerating', label: 'Accelerating', x: 0.28 },
  { key: 'peak',         label: 'Peak',         x: 0.50 },
  { key: 'saturation',   label: 'Saturation',   x: 0.65 },
  { key: 'decline',      label: 'Decline',      x: 0.80 },
  { key: 'dormant',      label: 'Dormant',      x: 0.93 },
]

const W = 700
const CURVE_TOP = 12
const CURVE_BOTTOM = 80

function bell(xNorm) {
  return Math.exp(-0.5 * Math.pow((xNorm - 0.5) / 0.18, 2))
}

function curveY(xNorm) {
  return CURVE_BOTTOM - (CURVE_BOTTOM - CURVE_TOP) * bell(xNorm)
}

const curvePoints = Array.from({ length: 101 }, (_, i) => {
  const xNorm = i / 100
  return `${(xNorm * W).toFixed(1)},${curveY(xNorm).toFixed(1)}`
})
const curvePath = `M ${curvePoints.join(' L ')}`
const fillPath = `M 0,${CURVE_BOTTOM} L ${curvePoints.join(' L ')} L ${W},${CURVE_BOTTOM} Z`

export default function TrendCycleIndicator({ stage }) {
  const normalizedStage = (stage || '').toLowerCase()
  const activeIdx = STAGES.findIndex(s => s.key === normalizedStage)

  return (
    <div className="trend-cycle">
      <p className="trend-cycle__title">Lifecycle Position <InfoTooltip text="Where this trend sits in its market cycle: Emerging → Accelerating → Peak → Saturation → Decline → Dormant. Based on search volume level and growth trajectory." /></p>

      {/* SVG curve — fills full width via preserveAspectRatio none, fixed height */}
      <svg
        viewBox={`0 0 ${W} ${CURVE_BOTTOM + 6}`}
        width="100%"
        height="110"
        preserveAspectRatio="none"
        aria-hidden="true"
        className="trend-cycle__svg"
      >
        <defs>
          <linearGradient id="tcGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#111111" stopOpacity="0.10" />
            <stop offset="100%" stopColor="#111111" stopOpacity="0.01" />
          </linearGradient>
        </defs>

        <path d={fillPath} fill="url(#tcGrad)" />
        <line x1="0" y1={CURVE_BOTTOM} x2={W} y2={CURVE_BOTTOM} stroke="#e8e8e8" strokeWidth="1.5" />
        <path d={curvePath} fill="none" stroke="#c8cdd8" strokeWidth="2" strokeLinejoin="round" />

        {STAGES.map((s, i) => {
          const cx = s.x * W
          const cy = curveY(s.x)
          const isActive = i === activeIdx
          const isPast = activeIdx >= 0 && i < activeIdx

          return (
            <g key={s.key}>
              <line
                x1={cx} y1={cy + (isActive ? 8 : 5)}
                x2={cx} y2={CURVE_BOTTOM}
                stroke={isActive ? '#cc3333' : '#e0e0e0'}
                strokeWidth={isActive ? 2 : 1}
                strokeDasharray={isActive ? 'none' : '4,3'}
              />
              <circle
                cx={cx} cy={cy}
                r={isActive ? 8 : 4}
                fill={isActive ? '#cc3333' : '#d0d5e0'}
                stroke={isActive ? '#fff' : 'none'}
                strokeWidth={isActive ? 2.5 : 0}
              />
              {isActive && (
                <circle
                  cx={cx} cy={cy} r={13}
                  fill="none"
                  stroke="#cc3333"
                  strokeWidth="1.5"
                  opacity="0.35"
                  className="trend-cycle__pulse"
                />
              )}
            </g>
          )
        })}
      </svg>

      {/* Labels rendered in HTML so they don't stretch with the SVG */}
      <div className="trend-cycle__labels">
        {STAGES.map((s, i) => (
          <span
            key={s.key}
            className={`trend-cycle__label${i === activeIdx ? ' trend-cycle__label--active' : ''}`}
            style={{ left: `${s.x * 100}%` }}
          >
            {s.label}
          </span>
        ))}
      </div>
    </div>
  )
}
