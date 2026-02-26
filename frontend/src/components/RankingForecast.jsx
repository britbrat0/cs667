import { useState, useEffect } from 'react'
import api from '../services/api'
import './RankingForecast.css'

function RankDelta({ delta }) {
  if (delta > 0) return <span className="rank-delta rank-delta--up">▲ {delta}</span>
  if (delta < 0) return <span className="rank-delta rank-delta--down">▼ {Math.abs(delta)}</span>
  return <span className="rank-delta rank-delta--flat">↔</span>
}

function SlopeBadge({ slope }) {
  if (slope > 2) return <span className="slope-badge slope-badge--strong-up">⬆ surging</span>
  if (slope > 0.5) return <span className="slope-badge slope-badge--up">↑ rising</span>
  if (slope < -2) return <span className="slope-badge slope-badge--strong-down">⬇ fading</span>
  if (slope < -0.5) return <span className="slope-badge slope-badge--down">↓ cooling</span>
  return <span className="slope-badge slope-badge--flat">→ stable</span>
}

export default function RankingForecast({ period }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    api
      .get('/trends/ranking-forecast', { params: { period } })
      .then(res => setData(res.data))
      .catch(() => setError('Failed to load forecast.'))
      .finally(() => setLoading(false))
  }, [period])

  if (loading) {
    return (
      <div className="ranking-forecast ranking-forecast--loading">
        <div className="ranking-forecast__shimmer" />
        <div className="ranking-forecast__shimmer ranking-forecast__shimmer--short" />
      </div>
    )
  }

  if (error || !data) {
    return <p className="ranking-forecast__error">{error || 'No forecast data available.'}</p>
  }

  const { top10, challengers, horizon_days } = data

  return (
    <div className="ranking-forecast">
      <div className="ranking-forecast__section">
        <h3 className="ranking-forecast__title">
          {horizon_days}-Day Ranking Forecast
          <span className="ranking-forecast__subtitle">Based on search volume trajectory</span>
        </h3>

        <div className="rf-table">
          <div className="rf-table__head">
            <span>Trend</span>
            <span>Now → Projected</span>
            <span>Change</span>
            <span>Momentum</span>
            <span>Stage</span>
          </div>
          {top10.map(kw => (
            <div key={kw.keyword} className={`rf-row ${kw.stage_warning ? 'rf-row--warned' : ''}`}>
              <span className="rf-row__keyword">{kw.keyword}</span>
              <span className="rf-row__ranks">
                <span className="rf-rank rf-rank--current">#{kw.current_rank}</span>
                <span className="rf-arrow">→</span>
                <span className={`rf-rank rf-rank--projected ${kw.projected_rank < kw.current_rank ? 'rf-rank--up' : kw.projected_rank > kw.current_rank ? 'rf-rank--down' : ''}`}>
                  #{kw.projected_rank}
                </span>
              </span>
              <span className="rf-row__delta">
                <RankDelta delta={kw.rank_delta} />
              </span>
              <span className="rf-row__slope">
                <SlopeBadge slope={kw.slope} />
              </span>
              <span className="rf-row__stage">
                <span className="rf-stage-pill">{kw.lifecycle_stage}</span>
                {kw.stage_warning && (
                  <span className="rf-stage-warning" title={kw.stage_warning}>⚠ {kw.stage_warning}</span>
                )}
              </span>
            </div>
          ))}
        </div>
      </div>

      {challengers.length > 0 && (
        <div className="ranking-forecast__section ranking-forecast__challengers">
          <h3 className="ranking-forecast__title">
            Rising Challengers
            <span className="ranking-forecast__subtitle">Tracked trends with upward momentum — may enter top 10</span>
          </h3>
          <div className="rf-table">
            {challengers.map(kw => (
              <div key={kw.keyword} className={`rf-row rf-row--challenger ${kw.stage_warning ? 'rf-row--warned' : ''}`}>
                <span className="rf-row__keyword">{kw.keyword}</span>
                <span className="rf-row__ranks">
                  <span className="rf-rank rf-rank--current">#{kw.current_rank}</span>
                  <span className="rf-arrow">→</span>
                  <span className={`rf-rank ${kw.projected_rank < kw.current_rank ? 'rf-rank--up' : ''}`}>
                    #{kw.projected_rank}
                  </span>
                </span>
                <span className="rf-row__delta">
                  <RankDelta delta={kw.rank_delta} />
                </span>
                <span className="rf-row__slope">
                  <SlopeBadge slope={kw.slope} />
                </span>
                <span className="rf-row__stage">
                  <span className="rf-stage-pill">{kw.lifecycle_stage}</span>
                  {kw.stage_warning && (
                    <span className="rf-stage-warning">⚠ {kw.stage_warning}</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
