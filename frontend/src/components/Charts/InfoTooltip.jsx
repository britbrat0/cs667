import { useState } from 'react'
import './InfoTooltip.css'

export default function InfoTooltip({ text }) {
  const [visible, setVisible] = useState(false)

  return (
    <span className="info-tip">
      <button
        className="info-tip__btn"
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
        onClick={(e) => e.stopPropagation()}
        type="button"
        aria-label="More information"
      >
        ⓘ
      </button>
      {visible && (
        <span className="info-tip__box" role="tooltip">
          {text}
        </span>
      )}
    </span>
  )
}
