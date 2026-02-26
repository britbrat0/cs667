import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LabelList,
} from 'recharts'

export default function SalesVolumeChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="chart-empty">No sales volume data available</p>
  }

  const sparse = data.length < 3

  const formatted = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    sold: Math.round(d.value),
  }))

  return (
    <div className="chart-container">
      <h4>Sales Volume Over Time</h4>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Bar dataKey="sold" fill="#111111" radius={[4, 4, 0, 0]}>
            {sparse && <LabelList dataKey="sold" position="top" style={{ fontSize: 11, fill: '#555' }} />}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
