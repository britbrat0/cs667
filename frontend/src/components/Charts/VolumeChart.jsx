import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LabelList,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'

export default function VolumeChart({ data, forecastData }) {
  if (!data || data.length === 0) {
    return <p className="chart-empty">No search volume data available</p>
  }

  const sparse = data.length < 3 && !forecastData

  // Build combined dataset for chart
  const formatted = data.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    value: d.value,
  }))

  if (!forecastData || forecastData.length === 0) {
    return (
      <div className="chart-container">
        <h4>Search Volume Over Time</h4>
        <ResponsiveContainer width="100%" height={250}>
          <ComposedChart data={formatted}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#1a1a2e"
              strokeWidth={2}
              dot={sparse ? { r: 5, fill: '#1a1a2e' } : false}
              activeDot={{ r: 4 }}
            >
              {sparse && <LabelList dataKey="value" position="top" style={{ fontSize: 11, fill: '#555' }} />}
            </Line>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    )
  }

  // Combine historical + forecast into one timeline
  // Connection point: duplicate last historical point as first forecast point
  const lastHistorical = formatted[formatted.length - 1]
  const forecastFormatted = forecastData.map((d) => ({
    date: new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    forecast: d.value,
    lower: d.lower,
    upper: d.upper,
  }))

  // Mark the boundary date for a reference line
  const boundaryDate = lastHistorical.date

  const combined = [
    ...formatted,
    // Attach forecast to the last historical point so lines connect
    { ...lastHistorical, forecast: lastHistorical.value, lower: forecastData[0].lower, upper: forecastData[0].upper },
    ...forecastFormatted,
  ]

  return (
    <div className="chart-container">
      <h4>Search Volume Over Time</h4>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={combined}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 12 }} domain={[0, 100]} />
          <Tooltip
            formatter={(val, name) => {
              if (name === 'value') return [val?.toFixed(1), 'Historical']
              if (name === 'forecast') return [val?.toFixed(1), 'Forecast']
              return null
            }}
            itemSorter={(a) => (a.name === 'value' ? -1 : 1)}
          />
          {/* Confidence band */}
          <Area
            type="monotone"
            dataKey="upper"
            stroke="none"
            fill="#2563eb"
            fillOpacity={0.1}
            legendType="none"
            tooltipType="none"
            isAnimationActive={false}
            activeDot={false}
          />
          <Area
            type="monotone"
            dataKey="lower"
            stroke="none"
            fill="#ffffff"
            fillOpacity={1}
            legendType="none"
            tooltipType="none"
            isAnimationActive={false}
            activeDot={false}
          />
          {/* Historical line */}
          <Line
            type="monotone"
            dataKey="value"
            stroke="#1a1a2e"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls={false}
          />
          {/* Forecast line */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#2563eb"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls={false}
          />
          {/* Vertical line at forecast boundary */}
          <ReferenceLine
            x={boundaryDate}
            stroke="#aaa"
            strokeDasharray="3 3"
            label={{ value: 'Today', position: 'insideTopRight', fontSize: 10, fill: '#aaa' }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
