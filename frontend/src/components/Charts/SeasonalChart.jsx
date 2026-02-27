import { BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ResponsiveContainer } from 'recharts'
import InfoTooltip from './InfoTooltip'

const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function buildFullYear(data) {
  const byMonth = {}
  for (const d of data) byMonth[d.month] = d
  return Array.from({ length: 12 }, (_, i) => {
    const m = i + 1
    return byMonth[m] ?? { month: m, label: MONTH_LABELS[i], avg: 0, std: 0, count: 0 }
  })
}

export default function SeasonalChart({ data }) {
  if (!data || data.length === 0) return null

  if (data.length < 3) {
    return (
      <div className="chart-container">
        <h4>Seasonal Pattern <InfoTooltip text="Average Google Trends search interest by calendar month, based on all available historical data. Highlighted bar = current month. Faded bars have no data yet." /></h4>
        <p style={{ color: '#888', fontSize: 13, padding: '12px 0' }}>
          Not enough historical data yet
        </p>
      </div>
    )
  }

  const currentMonth = new Date().getMonth() + 1
  const fullYear = buildFullYear(data)

  return (
    <div className="chart-container">
      <h4>Seasonal Pattern <InfoTooltip text="Average Google Trends search interest by calendar month, based on all available historical data. Highlighted bar = current month. Faded bars have no data yet." /></h4>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={fullYear}>
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#888' }} />
          <YAxis tick={{ fontSize: 11, fill: '#888' }} />
          <Tooltip
            contentStyle={{ background: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: 8 }}
            itemStyle={{ color: '#e0e0e0' }}
            labelStyle={{ color: '#aaa' }}
            formatter={(val, name) => {
              if (name === 'avg') return [val?.toFixed(1), 'Avg Volume']
              return [val?.toFixed(1), name]
            }}
          />
          <Bar dataKey="avg" name="avg" radius={[3, 3, 0, 0]}>
            {fullYear.map((entry) => (
              <Cell
                key={entry.month}
                fill={entry.month === currentMonth ? '#e75480' : '#f0a8b8'}
                fillOpacity={entry.count > 0 ? (entry.month === currentMonth ? 1 : 0.65) : 0.2}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
