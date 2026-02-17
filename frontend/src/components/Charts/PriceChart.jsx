import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts'

export default function PriceChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="chart-empty">No price data available</p>
  }

  const formatted = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    price: parseFloat(d.value.toFixed(2)),
  }))

  return (
    <div className="chart-container">
      <h4>eBay Avg Sold Price Over Time</h4>
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
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
