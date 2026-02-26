export default function VolatilityDisplay({ value }) {
  if (value === null || value === undefined) {
    return (
      <div className="chart-container">
        <h4>Price Volatility</h4>
        <p className="chart-empty">No volatility data available</p>
      </div>
    )
  }

  const level =
    value < 5 ? 'Low' : value < 15 ? 'Moderate' : value < 30 ? 'High' : 'Very High'

  const color =
    value < 5 ? '#8a8a8a' : value < 15 ? '#e8a0aa' : value < 30 ? '#cc6677' : '#cc3333'

  return (
    <div className="chart-container">
      <h4>Price Volatility</h4>
      <div className="volatility-display">
        <div className="volatility-value" style={{ color }}>
          ${value.toFixed(2)}
        </div>
        <div className="volatility-label">
          Standard Deviation
        </div>
        <div className="volatility-level" style={{ backgroundColor: color }}>
          {level}
        </div>
      </div>
    </div>
  )
}
