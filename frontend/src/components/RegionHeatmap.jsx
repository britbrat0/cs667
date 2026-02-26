import { useState, useMemo } from 'react'
import {
  ComposableMap,
  Geographies,
  Geography,
} from 'react-simple-maps'
import { scaleLinear } from 'd3-scale'
import './RegionHeatmap.css'

const US_GEO_URL = 'https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json'

export default function RegionHeatmap({ usRegions }) {
  const [tooltip, setTooltip] = useState('')

  const regionMap = useMemo(() => {
    const map = {}
    if (usRegions) {
      usRegions.forEach((r) => {
        map[r.region.toLowerCase()] = r.value
      })
    }
    return map
  }, [usRegions])

  const maxValue = useMemo(() => {
    if (!usRegions || usRegions.length === 0) return 100
    return Math.max(...usRegions.map((r) => r.value), 1)
  }, [usRegions])

  const colorScale = scaleLinear()
    .domain([0, maxValue])
    .range(['#ffe8e8', '#cc3333'])

  if (!usRegions || usRegions.length === 0) {
    return (
      <div className="chart-container">
        <h4>US Region Heatmap</h4>
        <p className="chart-empty">No region data available</p>
      </div>
    )
  }

  const getValue = (geo) => {
    const name = (geo.properties.name || '').toLowerCase()
    return regionMap[name] || 0
  }

  return (
    <div className="chart-container">
      <h4>US Region Heatmap</h4>

      {tooltip && <div className="heatmap-tooltip">{tooltip}</div>}

      <ComposableMap
        projection="geoAlbersUsa"
        style={{ width: '100%', height: 'auto', maxHeight: '400px' }}
      >
        <Geographies geography={US_GEO_URL}>
          {({ geographies }) =>
            geographies.map((geo) => {
              const value = getValue(geo)
              const name = geo.properties.name || 'Unknown'
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={value > 0 ? colorScale(value) : '#f0f0f0'}
                  stroke="#ccc"
                  strokeWidth={0.5}
                  onMouseEnter={() => setTooltip(value > 0 ? `${name}: ${value}` : name)}
                  onMouseLeave={() => setTooltip('')}
                  style={{
                    hover: { fill: value > 0 ? '#cc3333' : '#ddd', outline: 'none' },
                    pressed: { outline: 'none' },
                    default: { outline: 'none' },
                  }}
                />
              )
            })
          }
        </Geographies>
      </ComposableMap>

      <div className="heatmap-legend">
        <span>Low interest</span>
        <div
          className="heatmap-gradient"
          style={{ background: 'linear-gradient(to right, #ffe8e8, #cc3333)' }}
        />
        <span>High interest</span>
      </div>
    </div>
  )
}
