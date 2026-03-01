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

function mergeByDate(newsData, redditSentiment, tiktokSentiment) {
  const map = {}
  for (const d of newsData) {
    const key = new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    map[key] = { date: key, news: d.value }
  }
  for (const d of redditSentiment) {
    const key = new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    map[key] = { ...(map[key] || { date: key }), reddit: d.value }
  }
  for (const d of tiktokSentiment) {
    const key = new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    map[key] = { ...(map[key] || { date: key }), tiktok: d.value }
  }
  return Object.values(map).sort((a, b) => (a.date < b.date ? -1 : 1))
}

export default function SentimentChart({ newsData = [], redditSentiment = [], tiktokSentiment = [] }) {
  const hasNews = newsData?.length > 0
  const hasReddit = redditSentiment?.length > 0
  const hasTiktok = tiktokSentiment?.length > 0
  if (!hasNews && !hasReddit && !hasTiktok) return null

  const data = mergeByDate(newsData || [], redditSentiment || [], tiktokSentiment || [])

  return (
    <div className="chart-container">
      <h4>Social &amp; Media Sentiment <InfoTooltip text="VADER sentiment score (−1 to +1) for each source. News & Blogs: tone of fashion media coverage. Reddit: community post sentiment. TikTok: video description sentiment. Positive = favorable, negative = critical." /></h4>
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
            formatter={(val, name) => [`${sentimentLabel(val)} (${val?.toFixed(3)})`, name]}
          />
          <ReferenceLine y={0} stroke="#555" strokeDasharray="4 2" />
          <Legend wrapperStyle={{ fontSize: 12, color: '#aaa' }} />
          {hasNews && (
            <Line
              type="monotone"
              dataKey="news"
              name="News & Blogs"
              stroke="#c94070"
              strokeWidth={2}
              dot={{ r: 3, fill: '#c94070' }}
              activeDot={{ r: 5 }}
            />
          )}
          {hasReddit && (
            <Line
              type="monotone"
              dataKey="reddit"
              name="Reddit"
              stroke="#f0a8b8"
              strokeWidth={2}
              dot={{ r: 3, fill: '#f0a8b8' }}
              activeDot={{ r: 5 }}
            />
          )}
          {hasTiktok && (
            <Line
              type="monotone"
              dataKey="tiktok"
              name="TikTok"
              stroke="#7c3aed"
              strokeWidth={2}
              dot={{ r: 3, fill: '#7c3aed' }}
              activeDot={{ r: 5 }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
