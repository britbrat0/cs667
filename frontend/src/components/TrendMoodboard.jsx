import { useState, useEffect } from 'react'
import api from '../services/api'
import './TrendMoodboard.css'

export default function TrendMoodboard({ keyword }) {
  const [images, setImages] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!keyword) return
    setLoading(true)
    api
      .get(`/trends/${encodeURIComponent(keyword)}/images`, { params: { _t: Date.now() } })
      .then((res) => setImages(res.data.images || []))
      .catch(() => setImages([]))
      .finally(() => setLoading(false))
  }, [keyword])

  if (loading) {
    return (
      <div className="moodboard">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="moodboard__item moodboard__skeleton" />
        ))}
      </div>
    )
  }

  if (!images.length) return null

  return (
    <div className="moodboard">
      {images.map((img, i) => (
        <div key={i} className="moodboard__item">
          {img.item_url ? (
            <a href={img.item_url} target="_blank" rel="noopener noreferrer">
              <img src={img.image_url} alt={img.title || keyword} loading="lazy" />
            </a>
          ) : (
            <img src={img.image_url} alt={img.title || keyword} loading="lazy" />
          )}
          <span className={`moodboard__badge moodboard__badge--${img.source}`}>
            {img.source === 'ebay' ? 'eBay' : img.source === 'pinterest' ? 'Pinterest' : 'Pexels'}
          </span>
        </div>
      ))}
    </div>
  )
}
