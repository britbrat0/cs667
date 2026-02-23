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

export default function PriceChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="chart-empty">No price data available</p>
  }

  const sparse = data.length < 3

  const formatted = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    price: parseFloat(d.value.toFixed(2)),
  }))

  return (
    <div className="chart-container">
      <h4>Avg Sold Price Over Time</h4>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `$${v}`} />
          <Tooltip formatter={(v) => [`$${v}`, 'Avg Price']} />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#e74c3c"
            strokeWidth={2}
            dot={sparse ? { r: 5, fill: '#e74c3c' } : false}
            activeDot={{ r: 4 }}
          >
            {sparse && <LabelList dataKey="price" position="top" formatter={(v) => `$${v}`} style={{ fontSize: 11, fill: '#555' }} />}
          </Line>
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
