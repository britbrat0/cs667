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

/**
 * Merge multiple sentiment series by date, averaging values where multiple
 * sources exist on the same day. Each series is [{date, value}].
 */
function mergeSentimentByDate(...series) {
  const map = {}
  for (const source of series) {
    for (const d of source) {
      const key = new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      if (!map[key]) map[key] = { date: key, total: 0, count: 0 }
      map[key].total += d.value
      map[key].count += 1
    }
  }
  return Object.values(map)
    .map(d => ({ date: d.date, value: d.total / d.count }))
    .sort((a, b) => (a.date < b.date ? -1 : 1))
}

export default function SentimentChart({ newsData = [], redditSentiment = [], tiktokSentiment = [] }) {
  const allEmpty = !newsData?.length && !redditSentiment?.length && !tiktokSentiment?.length
  if (allEmpty) return null

  const data = mergeSentimentByDate(
    newsData || [],
    redditSentiment || [],
    tiktokSentiment || [],
  )

  const avg = data.reduce((s, d) => s + d.value, 0) / data.length
  const stroke = avg > 0.05 ? '#f0a8b8' : avg < -0.05 ? '#cc3333' : '#aaaaaa'

  return (
    <div className="chart-container">
      <h4>Media Sentiment <InfoTooltip text="Average VADER sentiment score (−1 to +1) across news & blog articles, Reddit posts, and TikTok content. Positive = favorable coverage of this trend. Negative = criticism or backlash." /></h4>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
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
            formatter={(val) => [`${sentimentLabel(val)} (${val?.toFixed(3)})`, 'Media Sentiment']}
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
