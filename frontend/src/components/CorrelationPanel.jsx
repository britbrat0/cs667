import { useState, useEffect } from 'react'
import api from '../services/api'
import InfoTooltip from './Charts/InfoTooltip'

export default function CorrelationPanel({ keyword, period = 30, onSearch }) {
  const [correlations, setCorrelations] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!keyword) return
    setLoading(true)
    api
      .get(`/trends/${encodeURIComponent(keyword)}/correlations`, { params: { period } })
      .then((res) => setCorrelations(res.data.correlations || []))
      .catch(() => setCorrelations([]))
      .finally(() => setLoading(false))
  }, [keyword, period])

  if (loading) return null
  if (!correlations.length) return null

  return (
    <div className="chart-container">
      <h4>Moves With <InfoTooltip text="Keywords whose search volume moves in sync with this one (Pearson r correlation). Positive = rise and fall together. Click any keyword to explore it." /></h4>
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {correlations.map((item) => {
          const pct = Math.abs(item.correlation) * 100
          const barColor = item.correlation > 0.1 ? '#4caf50' : '#888888'
          return (
            <li
              key={item.keyword}
              style={{ marginBottom: 10, cursor: 'pointer' }}
              onClick={() => onSearch && onSearch(item.keyword)}
              title={`r = ${item.correlation}`}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                <span style={{ fontSize: 13, color: '#e0e0e0' }}>{item.keyword}</span>
                <span style={{ fontSize: 12, color: '#888' }}>
                  {item.correlation > 0 ? '+' : ''}{item.correlation.toFixed(2)}
                </span>
              </div>
              <div style={{ background: '#2a2a2a', borderRadius: 4, height: 6, overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${pct}%`,
                    height: '100%',
                    background: barColor,
                    borderRadius: 4,
                    transition: 'width 0.4s ease',
                  }}
                />
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
