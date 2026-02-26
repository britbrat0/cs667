import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
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
            <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#888' }} />
            <YAxis tick={{ fontSize: 12, fill: '#888' }} />
            <Tooltip
              contentStyle={{ background: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: 8 }}
              itemStyle={{ color: '#e0e0e0' }}
              labelStyle={{ color: '#aaa' }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#f0a8b8"
              strokeWidth={2}
              dot={sparse ? { r: 5, fill: '#f0a8b8' } : false}
              activeDot={{ r: 4 }}
            >
              {sparse && <LabelList dataKey="value" position="top" style={{ fontSize: 11, fill: '#888' }} />}
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
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#888' }} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 12, fill: '#888' }} domain={[0, 100]} />
          <Tooltip
            contentStyle={{ background: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: 8 }}
            itemStyle={{ color: '#e0e0e0' }}
            labelStyle={{ color: '#aaa' }}
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
            fill="#cc3333"
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
            fill="#1e1e1e"
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
            stroke="#f0a8b8"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            connectNulls={false}
          />
          {/* Forecast line */}
          <Line
            type="monotone"
            dataKey="forecast"
            stroke="#cc3333"
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
