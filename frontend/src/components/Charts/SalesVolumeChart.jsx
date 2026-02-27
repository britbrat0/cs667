import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  LabelList,
} from 'recharts'
import InfoTooltip from './InfoTooltip'

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
      <h4>Sales Volume Over Time <InfoTooltip text="Combined sold listing count and active listing count per day across eBay, Etsy, Poshmark, and Depop." /></h4>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={formatted}>
          <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#888' }} />
          <YAxis tick={{ fontSize: 12, fill: '#888' }} />
          <Tooltip
            contentStyle={{ background: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: 8 }}
            itemStyle={{ color: '#e0e0e0' }}
            labelStyle={{ color: '#aaa' }}
          />
          <Bar dataKey="sold" fill="#cc3333" radius={[4, 4, 0, 0]}>
            {sparse && <LabelList dataKey="sold" position="top" style={{ fontSize: 11, fill: '#888' }} />}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
