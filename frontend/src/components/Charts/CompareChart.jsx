import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = ['#cc3333', '#7c3aed', '#db2777', '#0891b2', '#b45309', '#0f766e']

export default function CompareChart({ series }) {
  if (!series || series.length === 0) return null

  // Merge all dates across all keywords into one timeline
  const dateMap = {}
  series.forEach(({ keyword, volume }) => {
    volume.forEach(({ date, value }) => {
      const d = date.split('T')[0]
      if (!dateMap[d]) dateMap[d] = { date: d }
      dateMap[d][keyword] = value
    })
  })

  const data = Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date))

  if (data.length === 0) return (
    <p className="compare-no-data">Not enough data yet — search these keywords to trigger scraping.</p>
  )

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#888' }} />
        <YAxis tick={{ fontSize: 11, fill: '#888' }} />
        <Tooltip
          contentStyle={{ background: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: 8, fontSize: 12 }}
          itemStyle={{ color: '#e0e0e0' }}
          labelStyle={{ color: '#aaa' }}
          formatter={(value, name) => [value, name]}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: '#aaa' }} />
        {series.map(({ keyword }, i) => (
          <Line
            key={keyword}
            type="monotone"
            dataKey={keyword}
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
            dot={false}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
