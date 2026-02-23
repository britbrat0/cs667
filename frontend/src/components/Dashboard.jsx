import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../hooks/useAuth'
import api from '../services/api'
import TrendCard from './TrendCard'
import TrendDetail from './TrendDetail'
import CompareSection from './CompareSection'
import './Dashboard.css'

export default function Dashboard() {
  const { logout } = useAuth()
  const [period, setPeriod] = useState(7)
  const [searchQuery, setSearchQuery] = useState('')
  const [trends, setTrends] = useState([])
  const [loading, setLoading] = useState(true)
  const [expandedKeyword, setExpandedKeyword] = useState(null)
  const [searchResult, setSearchResult] = useState(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [view, setView] = useState('top') // 'top', 'search', or 'compare'
  const [compareKeywords, setCompareKeywords] = useState([])
  const compareSectionRef = useRef(null)

  useEffect(() => {
    fetchTopTrends()
  }, [period])

  const fetchTopTrends = async () => {
    setLoading(true)
    try {
      const res = await api.get('/trends/top', { params: { period } })
      setTrends(res.data.trends || [])
    } catch {
      setTrends([])
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchQuery.trim()) return
    setSearchLoading(true)
    setView('search')
    setExpandedKeyword(null)

    try {
      const res = await api.get('/trends/search', {
        params: { keyword: searchQuery.trim(), period },
      })
      setSearchResult(res.data)
    } catch {
      setSearchResult(null)
    } finally {
      setSearchLoading(false)
    }
  }

  const handleBackToTop = () => {
    setView('top')
    setSearchResult(null)
    setSearchQuery('')
    setExpandedKeyword(null)
  }

  const handleCardClick = (keyword) => {
    setExpandedKeyword(expandedKeyword === keyword ? null : keyword)
  }

  const handleRemoveKeyword = async (keyword) => {
    try {
      await api.delete(`/trends/keywords/${encodeURIComponent(keyword)}`)
      setTrends(trends.filter(t => t.keyword !== keyword))
      if (expandedKeyword === keyword) setExpandedKeyword(null)
    } catch {
      // Silently fail — seed keyword protection will show nothing
    }
  }

  const handleCompare = async (keyword) => {
    const kw = keyword.toLowerCase().trim()
    const isInCompare = compareKeywords.includes(kw)
    try {
      if (isInCompare) {
        await api.delete(`/compare/${encodeURIComponent(kw)}`)
        setCompareKeywords(prev => prev.filter(k => k !== kw))
      } else {
        await api.post(`/compare/${encodeURIComponent(kw)}`)
        setCompareKeywords(prev => [...prev, kw])
        setView('compare')
        setTimeout(() => compareSectionRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
      }
    } catch {
      // ignore
    }
  }

  // Sync compareKeywords from backend on mount
  useEffect(() => {
    api.get('/compare').then(res => {
      setCompareKeywords((res.data.keywords || []))
    }).catch(() => {})
  }, [])

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Fashion Trend Forecaster</h1>
        <button onClick={logout} className="logout-btn">Sign Out</button>
      </header>

      <div className="controls-bar">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Search a trend (e.g., vintage denim)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button type="submit" className="search-btn" disabled={searchLoading}>
            {searchLoading ? 'Searching...' : 'Search'}
          </button>
        </form>

        <select
          value={period}
          onChange={(e) => setPeriod(Number(e.target.value))}
          className="period-select"
        >
          <option value={7}>Past 7 days</option>
          <option value={14}>Past 14 days</option>
          <option value={30}>Past 30 days</option>
          <option value={60}>Past 60 days</option>
          <option value={90}>Past 90 days</option>
        </select>
      </div>

      <main className="dashboard-content">
        <div className="dashboard-tabs">
          <button
            className={`dashboard-tab ${view !== 'search' && view !== 'compare' ? 'dashboard-tab--active' : ''}`}
            onClick={() => { setView('top'); setSearchResult(null); setSearchQuery(''); setExpandedKeyword(null) }}
          >
            Top 10 Trends
          </button>
          <button
            className={`dashboard-tab ${view === 'compare' ? 'dashboard-tab--active' : ''}`}
            onClick={() => setView('compare')}
          >
            Compare
            {compareKeywords.length > 0 && (
              <span className="dashboard-tab__badge">{compareKeywords.length}</span>
            )}
          </button>
        </div>

        {view === 'search' ? (
          <div className="search-results">
            <div className="search-results__header">
              <h2>
                Search Results: <span className="search-keyword">{searchResult?.keyword || searchQuery}</span>
              </h2>
              <button onClick={handleBackToTop} className="back-btn">
                Back to Top Trends
              </button>
            </div>

            {searchLoading && <p className="status-message">Scraping data for "{searchQuery}"... This may take a moment.</p>}

            {!searchLoading && searchResult && (
              <TrendDetail keyword={searchResult.keyword} period={period} />
            )}

            {!searchLoading && !searchResult && (
              <p className="status-message">No results found. Try a different keyword.</p>
            )}
          </div>
        ) : view === 'compare' ? (
          <div ref={compareSectionRef}>
            <CompareSection
              compareKeywords={compareKeywords}
              onKeywordsChange={setCompareKeywords}
            />
          </div>
        ) : (
          <>
            {loading && <p className="status-message">Loading trends...</p>}

            {!loading && trends.length === 0 && (
              <div className="empty-state">
                <p className="status-message">No trend data available yet.</p>
                <p className="status-detail">
                  The scheduler will scrape data automatically every 6 hours.
                  You can also search for a specific trend above to trigger an on-demand scrape.
                </p>
              </div>
            )}

            {!loading && trends.length > 0 && (
              <div className="trends-list">
                {trends.map((trend) => (
                  <div key={trend.keyword} className="trend-list-item">
                    <TrendCard
                      trend={trend}
                      isExpanded={expandedKeyword === trend.keyword}
                      onClick={() => handleCardClick(trend.keyword)}
                      onRemove={handleRemoveKeyword}
                      onCompare={handleCompare}
                      inCompare={compareKeywords.includes(trend.keyword.toLowerCase())}
                    />
                    {expandedKeyword === trend.keyword && (
                      <TrendDetail keyword={trend.keyword} period={period} />
                    )}
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
