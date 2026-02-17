import { useState, useMemo } from 'react'
import {
  ComposableMap,
  Geographies,
  Geography,
  ZoomableGroup,
} from 'react-simple-maps'
import { scaleLinear } from 'd3-scale'
import './RegionHeatmap.css'

const US_GEO_URL = 'https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json'
const WORLD_GEO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

export default function RegionHeatmap({ usRegions, globalRegions }) {
  const [scope, setScope] = useState('us')
  const [tooltip, setTooltip] = useState('')

  const regions = scope === 'us' ? usRegions : globalRegions
  const geoUrl = scope === 'us' ? US_GEO_URL : WORLD_GEO_URL

  const regionMap = useMemo(() => {
    const map = {}
    if (regions) {
      regions.forEach((r) => {
        // Store both lowercase and original for flexible matching
        map[r.region.toLowerCase()] = r.value
      })
    }
    return map
  }, [regions])

  const maxValue = useMemo(() => {
    if (!regions || regions.length === 0) return 100
    return Math.max(...regions.map((r) => r.value), 1)
  }, [regions])

  const colorScale = scaleLinear()
    .domain([0, maxValue])
    .range(['#e8eaf6', '#1a1a2e'])

  const hasUsData = usRegions && usRegions.length > 0
  const hasGlobalData = globalRegions && globalRegions.length > 0

  if (!hasUsData && !hasGlobalData) {
    return (
      <div className="chart-container">
        <h4>Region Heatmap</h4>
        <p className="chart-empty">No region data available</p>
      </div>
    )
  }

  // Match geography name to region data
  const getValue = (geo) => {
    const name = (geo.properties.name || '').toLowerCase()
    return regionMap[name] || 0
  }

  return (
    <div className="chart-container">
      <div className="heatmap-header">
        <h4>Region Heatmap</h4>
        <div className="heatmap-toggle">
          <button
            className={scope === 'us' ? 'active' : ''}
            onClick={() => setScope('us')}
            disabled={!hasUsData}
          >
            US States
          </button>
          <button
            className={scope === 'global' ? 'active' : ''}
            onClick={() => setScope('global')}
            disabled={!hasGlobalData}
          >
            Global
          </button>
        </div>
      </div>

      {tooltip && <div className="heatmap-tooltip">{tooltip}</div>}

      {((scope === 'us' && !hasUsData) || (scope === 'global' && !hasGlobalData)) ? (
        <p className="chart-empty">No {scope === 'us' ? 'US' : 'global'} region data available. Try the other view.</p>
      ) : (
        <>
          <ComposableMap
            projection={scope === 'us' ? 'geoAlbersUsa' : 'geoEqualEarth'}
            projectionConfig={scope === 'us' ? {} : { scale: 160, center: [0, 0] }}
            style={{ width: '100%', height: 'auto', maxHeight: '400px' }}
          >
            {scope !== 'us' && <ZoomableGroup>
              <Geographies geography={geoUrl}>
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
                          hover: { fill: value > 0 ? '#16213e' : '#ddd', outline: 'none' },
                          pressed: { outline: 'none' },
                          default: { outline: 'none' },
                        }}
                      />
                    )
                  })
                }
              </Geographies>
            </ZoomableGroup>}
            {scope === 'us' && (
              <Geographies geography={geoUrl}>
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
                          hover: { fill: value > 0 ? '#16213e' : '#ddd', outline: 'none' },
                          pressed: { outline: 'none' },
                          default: { outline: 'none' },
                        }}
                      />
                    )
                  })
                }
              </Geographies>
            )}
          </ComposableMap>

          <div className="heatmap-legend">
            <span>Low interest</span>
            <div
              className="heatmap-gradient"
              style={{
                background: 'linear-gradient(to right, #e8eaf6, #1a1a2e)',
              }}
            />
            <span>High interest</span>
          </div>
        </>
      )}
    </div>
  )
}
