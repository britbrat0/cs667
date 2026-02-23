import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const COLORS = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']

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
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8 }}
          formatter={(value, name) => [value, name]}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
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
