import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts'
import InfoTooltip from './InfoTooltip'

function sentimentLabel(value) {
  if (value > 0.05) return 'Positive'
  if (value < -0.05) return 'Negative'
  return 'Neutral'
}

export default function SentimentChart({ data }) {
  if (!data || data.length === 0) return null

  const avg = data.reduce((s, d) => s + d.value, 0) / data.length
  const stroke = avg > 0.05 ? '#4caf50' : avg < -0.05 ? '#cc3333' : '#aaaaaa'

  const formatted = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: d.value,
  }))

  return (
    <div className="chart-container">
      <h4>eBay Listing Sentiment <InfoTooltip text="VADER sentiment score of eBay listing titles (−1 to +1). Positive = enthusiastic or premium language. Negative = discount or clearance language." /></h4>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={formatted}>
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#888' }} />
          <YAxis
            domain={[-1, 1]}
            tick={{ fontSize: 11, fill: '#888' }}
            tickFormatter={(v) => v.toFixed(1)}
          />
          <Tooltip
            contentStyle={{ background: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: 8 }}
            itemStyle={{ color: '#e0e0e0' }}
            labelStyle={{ color: '#aaa' }}
            formatter={(val) => [sentimentLabel(val), `Score: ${val?.toFixed(3)}`]}
          />
          <ReferenceLine y={0} stroke="#555" strokeDasharray="4 2" />
          <Line
            type="monotone"
            dataKey="value"
            stroke={stroke}
            strokeWidth={2}
            dot={{ r: 3, fill: stroke }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
