import { useState, useEffect } from 'react'
import api from '../services/api'
import VolumeChart from './Charts/VolumeChart'
import PriceChart from './Charts/PriceChart'
import SalesVolumeChart from './Charts/SalesVolumeChart'
import VolatilityDisplay from './Charts/VolatilityDisplay'
import RegionHeatmap from './RegionHeatmap'
import LifecycleBadge from './LifecycleBadge'
import './TrendDetail.css'

export default function TrendDetail({ keyword, period }) {
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!keyword) return
    setLoading(true)
    api
      .get(`/trends/${encodeURIComponent(keyword)}/details`, { params: { period } })
      .then((res) => setDetails(res.data))
      .catch(() => setDetails(null))
      .finally(() => setLoading(false))
  }, [keyword, period])

  if (loading) {
    return <div className="trend-detail__loading">Loading trend details...</div>
  }

  if (!details) {
    return <div className="trend-detail__empty">No details available for "{keyword}"</div>
  }

  return (
    <div className="trend-detail">
      <div className="trend-detail__header">
        <h3>{keyword}</h3>
        {details.score?.lifecycle_stage && (
          <LifecycleBadge stage={details.score.lifecycle_stage} size="large" />
        )}
      </div>

      {details.score && (
        <div className="trend-detail__scores">
          <div className="score-item">
            <span className="score-label">Composite Score</span>
            <span className="score-value">
              {details.score.composite_score?.toFixed(1)}
            </span>
          </div>
          <div className="score-item">
            <span className="score-label">Volume Growth</span>
            <span className="score-value">
              {details.score.volume_growth?.toFixed(1)}%
            </span>
          </div>
          <div className="score-item">
            <span className="score-label">Price Growth</span>
            <span className="score-value">
              {details.score.price_growth?.toFixed(1)}%
            </span>
          </div>
        </div>
      )}

      <div className="trend-detail__charts">
        <VolumeChart data={details.search_volume} />
        <PriceChart data={details.ebay_avg_price} />
        <SalesVolumeChart data={details.sales_volume} />
        <VolatilityDisplay value={details.price_volatility} />
      </div>

      <RegionHeatmap
        usRegions={details.regions_us}
        globalRegions={details.regions_global}
      />
    </div>
  )
}
