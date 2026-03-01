import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import InfoTooltip from './InfoTooltip'

function sentimentLabel(value) {
  if (value > 0.05) return 'Positive'
  if (value < -0.05) return 'Negative'
  return 'Neutral'
}

function mergeByDate(ebay, news) {
  const map = {}
  for (const d of ebay) {
    const key = new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    map[key] = { date: key, ebay: d.value }
  }
  for (const d of news) {
    const key = new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    map[key] = { ...(map[key] || { date: key }), news: d.value }
  }
  return Object.values(map).sort((a, b) => (a.date < b.date ? -1 : 1))
}

export default function SentimentChart({ data, newsData = [] }) {
  const hasEbay = data && data.length > 0
  const hasNews = newsData && newsData.length > 0
  if (!hasEbay && !hasNews) return null

  const formatted = hasEbay || hasNews
    ? mergeByDate(hasEbay ? data : [], hasNews ? newsData : [])
    : []

  const ebayAvg = hasEbay ? data.reduce((s, d) => s + d.value, 0) / data.length : 0
  const ebayStroke = ebayAvg > 0.05 ? '#4caf50' : ebayAvg < -0.05 ? '#cc3333' : '#aaaaaa'

  return (
    <div className="chart-container">
      <h4>Sentiment <InfoTooltip text="VADER sentiment score (−1 to +1). eBay: enthusiasm or discount language in listing titles. News: tone of fashion media coverage. Positive = favorable coverage." /></h4>
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
            formatter={(val, name) => [
              `${sentimentLabel(val)} (${val?.toFixed(3)})`,
              name === 'ebay' ? 'eBay' : 'News',
            ]}
          />
          <ReferenceLine y={0} stroke="#555" strokeDasharray="4 2" />
          {(hasEbay || hasNews) && <Legend wrapperStyle={{ fontSize: 12, color: '#aaa' }} />}
          {hasEbay && (
            <Line
              type="monotone"
              dataKey="ebay"
              name="eBay"
              stroke={ebayStroke}
              strokeWidth={2}
              dot={{ r: 3, fill: ebayStroke }}
              activeDot={{ r: 5 }}
            />
          )}
          {hasNews && (
            <Line
              type="monotone"
              dataKey="news"
              name="News"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={{ r: 3, fill: '#f59e0b' }}
              activeDot={{ r: 5 }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
