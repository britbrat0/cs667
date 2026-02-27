import InfoTooltip from './InfoTooltip'

export default function SellThroughChart({ data }) {
  if (!data || data.rate == null) return null

  const { rate, sold_30d, active } = data

  let color = '#cc3333'
  if (rate >= 70) color = '#4caf50'
  else if (rate >= 40) color = '#cc8833'

  return (
    <div className="chart-container sell-through-card">
      <h4>Sell-Through Rate (30d) <InfoTooltip text="Share of total inventory (sold + active) that has sold in the last 30 days. Above 70% = strong demand. 40–70% = healthy. Below 40% = slow-moving." /></h4>
      <div style={{ textAlign: 'center', padding: '12px 0' }}>
        <div
          style={{
            fontSize: 48,
            fontWeight: 700,
            color,
            lineHeight: 1.1,
            letterSpacing: '-1px',
          }}
        >
          {rate.toFixed(1)}%
        </div>
        <div style={{ color: '#888', fontSize: 13, marginTop: 8 }}>
          {sold_30d} sold &nbsp;·&nbsp; {active} active listings
        </div>
      </div>
    </div>
  )
}
