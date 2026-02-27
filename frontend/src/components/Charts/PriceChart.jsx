import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  LabelList,
} from 'recharts'
import InfoTooltip from './InfoTooltip'

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
      <h4>Avg Sold Price Over Time <InfoTooltip text="Daily average selling price across eBay, Etsy, Poshmark, and Depop, averaged across all sources per day." /></h4>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={formatted}>
          <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#888' }} />
          <YAxis tick={{ fontSize: 12, fill: '#888' }} tickFormatter={(v) => `$${v}`} />
          <Tooltip
            formatter={(v) => [`$${v}`, 'Avg Price']}
            contentStyle={{ background: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: 8 }}
            itemStyle={{ color: '#e0e0e0' }}
            labelStyle={{ color: '#aaa' }}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#e74c3c"
            strokeWidth={2}
            dot={sparse ? { r: 5, fill: '#e74c3c' } : false}
            activeDot={{ r: 4 }}
          >
            {sparse && <LabelList dataKey="price" position="top" formatter={(v) => `$${v}`} style={{ fontSize: 11, fill: '#888' }} />}
          </Line>
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
