import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LabelList,
} from 'recharts'

export default function VolumeChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="chart-empty">No search volume data available</p>
  }

  const sparse = data.length < 3

  const formatted = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: d.value,
  }))

  return (
    <div className="chart-container">
      <h4>Search Volume Over Time</h4>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#1a1a2e"
            strokeWidth={2}
            dot={sparse ? { r: 5, fill: '#1a1a2e' } : false}
            activeDot={{ r: 4 }}
          >
            {sparse && <LabelList dataKey="value" position="top" style={{ fontSize: 11, fill: '#555' }} />}
          </Line>
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
