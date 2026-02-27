import InfoTooltip from './InfoTooltip'

export default function VolatilityDisplay({ value, cv }) {
  if (value === null || value === undefined) {
    return (
      <div className="chart-container">
        <h4>Price Volatility <InfoTooltip text="Standard deviation of prices across listings. CV% shows how spread out prices are relative to the average — higher means wider range across items." /></h4>
        <p className="chart-empty">No volatility data available</p>
      </div>
    )
  }

  // Use coefficient of variation (%) for the label — scale-invariant across price ranges.
  // Fall back to absolute $ thresholds only if avg price isn't available.
  const level = cv !== null && cv !== undefined
    ? (cv < 20 ? 'Low' : cv < 50 ? 'Moderate' : cv < 80 ? 'High' : 'Very High')
    : (value < 15 ? 'Low' : value < 40 ? 'Moderate' : value < 80 ? 'High' : 'Very High')

  const color =
    level === 'Low' ? '#8a8a8a' : level === 'Moderate' ? '#e8a0aa' : level === 'High' ? '#cc6677' : '#cc3333'

  return (
    <div className="chart-container">
      <h4>Price Volatility <InfoTooltip text="Standard deviation of prices across listings. CV% shows how spread out prices are relative to the average — higher means wider range across items." /></h4>
      <div className="volatility-display">
        <div className="volatility-value" style={{ color }}>
          ${value.toFixed(0)}
        </div>
        <div className="volatility-label">
          {cv !== null && cv !== undefined
            ? `std dev · ${cv.toFixed(1)}% of avg price`
            : 'Standard Deviation'}
        </div>
        <div className="volatility-level" style={{ backgroundColor: color }}>
          {level}
        </div>
      </div>
    </div>
  )
}
