import { useState, useEffect } from 'react'
import api from '../services/api'
import VolumeChart from './Charts/VolumeChart'
import PriceChart from './Charts/PriceChart'
import SalesVolumeChart from './Charts/SalesVolumeChart'
import VolatilityDisplay from './Charts/VolatilityDisplay'
import RegionHeatmap from './RegionHeatmap'
import LifecycleBadge from './LifecycleBadge'
import './TrendDetail.css'

const HORIZON_OPTIONS = [
  { label: '7 days', value: 7 },
  { label: '14 days', value: 14 },
  { label: '30 days', value: 30 },
]

export default function TrendDetail({ keyword, period }) {
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showForecast, setShowForecast] = useState(false)
  const [forecastHorizon, setForecastHorizon] = useState(14)
  const [forecastData, setForecastData] = useState(null)
  const [forecastLoading, setForecastLoading] = useState(false)
  const [forecastError, setForecastError] = useState('')

  useEffect(() => {
    if (!keyword) return
    setLoading(true)
    api
      .get(`/trends/${encodeURIComponent(keyword)}/details`, { params: { period } })
      .then((res) => setDetails(res.data))
      .catch(() => setDetails(null))
      .finally(() => setLoading(false))
  }, [keyword, period])

  useEffect(() => {
    if (!showForecast) return
    setForecastLoading(true)
    setForecastError('')
    api
      .get(`/trends/${encodeURIComponent(keyword)}/forecast`, { params: { horizon: forecastHorizon } })
      .then((res) => {
        if (res.data.insufficient_data) {
          setForecastError('Not enough historical data to generate a forecast yet.')
          setForecastData(null)
        } else {
          setForecastData(res.data.forecast)
        }
      })
      .catch(() => setForecastError('Failed to load forecast.'))
      .finally(() => setForecastLoading(false))
  }, [showForecast, forecastHorizon, keyword])

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
        {/* Search volume chart with forecast controls */}
        <div className="forecast-chart-wrapper">
          <div className="forecast-controls">
            <button
              className={`forecast-toggle ${showForecast ? 'forecast-toggle--active' : ''}`}
              onClick={() => setShowForecast(v => !v)}
            >
              {showForecast ? '✕ Hide Forecast' : '◆ Show Forecast'}
            </button>
            {showForecast && (
              <div className="forecast-horizon-tabs">
                {HORIZON_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    className={`forecast-horizon-tab ${forecastHorizon === opt.value ? 'forecast-horizon-tab--active' : ''}`}
                    onClick={() => setForecastHorizon(opt.value)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {showForecast && forecastLoading && (
            <p className="forecast-status">Generating forecast...</p>
          )}
          {showForecast && forecastError && (
            <p className="forecast-error">{forecastError}</p>
          )}

          <VolumeChart
            data={details.search_volume}
            forecastData={showForecast && !forecastLoading && !forecastError ? forecastData : null}
          />

          {showForecast && forecastData && (
            <p className="forecast-legend">
              <span className="forecast-legend__historical" /> Historical &nbsp;
              <span className="forecast-legend__forecast" /> Forecast &nbsp;
              <span className="forecast-legend__band" /> 95% confidence interval
            </p>
          )}
        </div>

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
