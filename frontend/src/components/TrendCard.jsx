import LifecycleBadge from './LifecycleBadge'
import './TrendCard.css'

export default function TrendCard({ trend, isExpanded, onClick }) {
  const scoreColor = trend.composite_score > 0 ? '#27ae60' : trend.composite_score < 0 ? '#e74c3c' : '#666'
  const scorePrefix = trend.composite_score > 0 ? '+' : ''

  return (
    <div
      className={`trend-card ${isExpanded ? 'trend-card--expanded' : ''}`}
      onClick={onClick}
    >
      <div className="trend-card__header">
        <span className="trend-card__rank">#{trend.rank}</span>
        <div className="trend-card__info">
          <span className="trend-card__keyword">{trend.keyword}</span>
          <div className="trend-card__meta">
            <span className="trend-card__score" style={{ color: scoreColor }}>
              {scorePrefix}{trend.composite_score?.toFixed(1)}
            </span>
            {trend.lifecycle_stage && (
              <LifecycleBadge stage={trend.lifecycle_stage} size="small" />
            )}
          </div>
        </div>
        <span className="trend-card__expand">
          {isExpanded ? '\u25B2' : '\u25BC'}
        </span>
      </div>

      {isExpanded && (
        <div className="trend-card__details-hint">
          <div className="trend-card__growth-row">
            <div className="trend-card__growth-item">
              <span className="growth-label">Volume Growth</span>
              <span className="growth-value" style={{ color: trend.volume_growth > 0 ? '#27ae60' : '#e74c3c' }}>
                {trend.volume_growth > 0 ? '+' : ''}{trend.volume_growth?.toFixed(1)}%
              </span>
            </div>
            <div className="trend-card__growth-item">
              <span className="growth-label">Price Growth</span>
              <span className="growth-value" style={{ color: trend.price_growth > 0 ? '#27ae60' : '#e74c3c' }}>
                {trend.price_growth > 0 ? '+' : ''}{trend.price_growth?.toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
