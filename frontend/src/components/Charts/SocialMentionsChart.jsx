import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import InfoTooltip from './InfoTooltip'

function mergeByDate(reddit, tiktok) {
  const map = {}
  for (const d of reddit) {
    const key = new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    map[key] = { date: key, reddit: d.count }
  }
  for (const d of tiktok) {
    const key = new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    if (map[key]) {
      map[key].tiktok = d.count
    } else {
      map[key] = { date: key, tiktok: d.count }
    }
  }
  return Object.values(map).sort((a, b) => (a.date < b.date ? -1 : 1))
}

export default function SocialMentionsChart({ reddit = [], tiktok = [] }) {
  if (!reddit?.length && !tiktok?.length) return null

  const data = mergeByDate(reddit, tiktok)

  return (
    <div className="chart-container">
      <h4>Social Mentions <InfoTooltip text="Daily post count mentioning this keyword on Reddit (bars) and TikTok (line). Signals grassroots community interest outside of search data." /></h4>
      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={data}>
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#888' }} />
          <YAxis tick={{ fontSize: 11, fill: '#888' }} />
          <Tooltip
            contentStyle={{ background: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: 8 }}
            itemStyle={{ color: '#e0e0e0' }}
            labelStyle={{ color: '#aaa' }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: '#aaa' }} />
          {reddit?.length > 0 && (
            <Bar dataKey="reddit" name="Reddit" fill="#f0a8b8" radius={[3, 3, 0, 0]} />
          )}
          {tiktok?.length > 0 && (
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
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
