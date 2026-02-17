# SYSTEM.md — Fashion Trend Forecasting Platform

## 1. Overview

A full-stack application that detects and predicts fashion resale trend cycles using open market and search data. The system aggregates signals from Google Trends, eBay sold listings, Reddit, and Depop to compute composite trend scores, surface the top emerging trends, and let users explore any fashion keyword in depth.

---

## 2. Architecture

### 2.1 High-Level Diagram

```
┌─────────────────────┐       ┌─────────────────────────────────────┐
│   Frontend Container│       │        Backend Container            │
│                     │       │                                     │
│  React App          │       │  FastAPI Server                     │
│  (Mobile-Adaptive)  │◄─────►│    ├── Auth Module (CSV-based)      │
│                     │ Nginx │    ├── Trend API                    │
│  Nginx (reverse     │ proxy │    ├── Scraper Service              │
│  proxy + static     │       │    ├── Scheduler (APScheduler)      │
│  file serving)      │       │    └── SQLite Database              │
└─────────────────────┘       └─────────────────────────────────────┘
```

### 2.2 Containers

| Container | Role | Tech |
|-----------|------|------|
| **frontend** | Serves React SPA, proxies `/api` requests to backend | Nginx + React (production build) |
| **backend** | REST API, scraping, scheduling, auth, data storage | FastAPI + Python |

### 2.3 Networking

- Nginx in the frontend container serves the React static build and reverse-proxies all `/api/*` requests to the backend container.
- Docker Compose creates a shared bridge network so the frontend container can reach the backend container by service name (e.g., `http://backend:8000`).

---

## 3. Frontend

### 3.1 Framework & Tooling

- **React** (with Vite for dev/build)
- **CSS**: Mobile-adaptive responsive design (CSS Grid/Flexbox, media queries — or a lightweight library like Tailwind CSS)
- **Charting**: Recharts or Chart.js for time-series graphs
- **Maps**: react-simple-maps or Leaflet for region heatmaps

### 3.2 Pages & Components

#### 3.2.1 Landing Page — Login/Registration

- Simple form with email + password fields
- Toggle between Login and Register modes
- On success, store JWT token in localStorage and redirect to Dashboard
- On failure, show inline error messages

#### 3.2.2 Dashboard

The main view after login. Composed of the following sections:

**A. Controls Bar (top)**

| Control | Description |
|---------|-------------|
| **Search Bar** | Text input for custom keyword search. Triggers on-demand scraping if the keyword is not already cached. |
| **Time Period Selector** | Dropdown or slider: 7 / 14 / 30 / 60 / 90 days. Defaults to 7 days. |

**B. Top 10 Emerging Trends (main content)**

- Default view: a ranked list/card grid of the top 10 trends by composite score growth over the selected time period.
- Each trend card shows:
  - **Rank** (1–10)
  - **Keyword** name
  - **Composite Score** value and delta (e.g., +23%)
  - **Lifecycle Stage** badge (Emerging, Accelerating, Peak, Saturation, Decline, Dormant)

- **Expanded view** (click/tap a card to expand):
  - **Search Volume Over Time** — line chart (Google Trends data)
  - **eBay Avg Sold Price Over Time** — line chart
  - **Sales Volume Over Time** — bar/line chart (eBay sold count)
  - **Price Volatility** — metric or mini chart (std dev or coefficient of variation of price)
  - **Region Heatmap** — choropleth map with toggle between US states and global countries
  - **Lifecycle Position** — visual indicator showing where this trend sits in the cycle

**C. Custom Search Results**

- When a user searches a custom keyword, the dashboard replaces the top-10 view with a single-trend deep dive using the same expanded view layout above.
- A "Back to Top Trends" button returns to the default view.

### 3.3 Mobile-Adaptive Design

- Breakpoints: mobile (<768px), tablet (768–1024px), desktop (>1024px)
- Cards stack vertically on mobile, grid on tablet/desktop
- Charts resize responsively
- Collapsible navigation/controls on small screens

### 3.4 Nginx Configuration (Frontend Container)

```
server {
    listen 80;

    # Serve React static build
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;  # SPA fallback
    }

    # Reverse proxy API calls to backend
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 4. Backend

### 4.1 Framework & Structure

- **FastAPI** (Python 3.11+)
- Project layout:

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry, router registration
│   ├── config.py             # Settings (env vars, paths, constants)
│   ├── models.py             # Pydantic models (request/response schemas)
│   ├── database.py           # SQLite connection and table setup
│   ├── auth/
│   │   ├── router.py         # /api/auth/login, /api/auth/register
│   │   ├── service.py        # Password hashing, JWT creation/validation
│   │   └── users.csv         # Local user store (email, hashed_password)
│   ├── trends/
│   │   ├── router.py         # /api/trends/top, /api/trends/search
│   │   ├── service.py        # Composite score calculation, lifecycle detection
│   │   └── schemas.py        # Trend-specific Pydantic models
│   ├── scrapers/
│   │   ├── google_trends.py  # pytrends wrapper
│   │   ├── ebay.py           # eBay sold listings scraper
│   │   ├── reddit.py         # Reddit fashion subreddit scraper
│   │   ├── depop.py          # Depop listing scraper
│   │   └── discovery.py      # Auto-discovery of new keywords
│   └── scheduler/
│       └── jobs.py           # APScheduler job definitions
├── data/
│   ├── trends.db             # SQLite database file
│   └── seed_keywords.json    # Curated seed keyword list
├── requirements.txt
└── Dockerfile
```

### 4.2 Authentication

- **Storage**: `users.csv` managed by pandas
  - Columns: `email`, `hashed_password`, `created_at`
- **Password hashing**: `bcrypt` via `passlib`
- **Session/token**: JWT tokens (via `python-jose`)
  - Issued on login/register, included as `Authorization: Bearer <token>` header
  - Token expiry: 24 hours
- **Endpoints**:
  - `POST /api/auth/register` — create user, return JWT
  - `POST /api/auth/login` — validate credentials, return JWT

### 4.3 Data Storage (SQLite)

#### Tables

**`trend_data`** — raw scraped data points

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| keyword | TEXT | Fashion keyword |
| source | TEXT | `google_trends`, `ebay`, `reddit`, `depop` |
| metric | TEXT | `search_volume`, `avg_price`, `sold_count`, `mention_count`, `listing_count` |
| value | REAL | Numeric value |
| region | TEXT | Region code (US state, country ISO) — nullable |
| recorded_at | TIMESTAMP | When the data point was captured |

**`keywords`** — tracked keywords registry

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| keyword | TEXT UNIQUE | The fashion keyword |
| source | TEXT | `seed`, `auto_discovered`, `user_search` |
| status | TEXT | `active`, `pending_review`, `inactive` |
| added_at | TIMESTAMP | When the keyword was added |

**`trend_scores`** — precomputed composite scores (refreshed by scheduler)

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| keyword | TEXT | Fashion keyword |
| period_days | INTEGER | Time window (7, 14, 30, 60, 90) |
| volume_growth | REAL | % growth in search/sales volume |
| price_growth | REAL | % growth in avg sold price |
| composite_score | REAL | 0.6 * volume_growth + 0.4 * price_growth |
| lifecycle_stage | TEXT | Emerging / Accelerating / Peak / Saturation / Decline / Dormant |
| computed_at | TIMESTAMP | When this score was last calculated |

### 4.4 Data Sources & Scrapers

#### 4.4.1 Google Trends

- **Library**: `pytrends` (unofficial Google Trends API)
- **Data collected**: Search interest over time (relative volume 0–100), interest by region (US states + worldwide)
- **Rate limiting**: Respect Google's implicit rate limits; add random delays between requests

#### 4.4.2 eBay Sold Listings

- **Method**: Web scraping eBay "Sold Items" search results (requests + BeautifulSoup)
- **Data collected**:
  - Sold price per item
  - Number of sold items (volume)
  - Date sold
- **Derived metrics**: Average sold price, sales volume, price standard deviation (volatility)

#### 4.4.3 Reddit

- **Method**: Reddit API (via `praw`) or scraping
- **Subreddits**: r/fashion, r/streetwear, r/malefashionadvice, r/femalefashionadvice, r/thriftstorehauls, r/Depop, r/VintageFashion (and similar)
- **Data collected**: Post/comment mention counts for tracked keywords, trending terms in titles
- **Auto-discovery**: Parse trending post titles and comments for new fashion keywords

#### 4.4.4 Depop

- **Method**: Web scraping Depop search/trending pages (requests + BeautifulSoup)
- **Data collected**:
  - Listing count for keyword
  - Listing prices
  - Sold status
- **Auto-discovery**: Scrape Depop's trending/explore page for emerging terms

### 4.5 Trend Discovery (Seed + Auto-Discovery)

1. **Seed list** (`data/seed_keywords.json`): A curated JSON array of fashion keywords to begin tracking (e.g., "vintage denim", "gorpcore", "quiet luxury", "ballet flats", "Y2K", "coquette").
2. **Auto-discovery**: The `discovery.py` module scans Reddit trending posts and Depop explore/trending pages, extracts candidate keywords using frequency analysis, and inserts them into the `keywords` table with `status = 'pending_review'`.
3. **Review flow**: Pending keywords can be promoted to `active` or marked `inactive` (future: admin UI; for now: manual DB update or simple API endpoint).

### 4.6 Scheduling (APScheduler)

| Job | Frequency | Description |
|-----|-----------|-------------|
| **scrape_all_sources** | Every 6 hours | Scrape Google Trends, eBay, Reddit, Depop for all `active` keywords. Insert raw data into `trend_data`. |
| **compute_scores** | Every 6 hours (after scrape) | Recalculate composite scores and lifecycle stages for all active keywords across all time periods. Update `trend_scores`. |
| **discover_keywords** | Every 24 hours | Run auto-discovery on Reddit and Depop. Insert new candidates as `pending_review`. |

### 4.7 Composite Score Calculation

```
composite_score = 0.6 * volume_growth + 0.4 * price_growth
```

- **volume_growth**: Percentage change in combined search volume (Google) + sales volume (eBay) + mention count (Reddit) + listing count (Depop) between the first half and second half of the selected time window.
- **price_growth**: Percentage change in eBay average sold price between the first half and second half of the selected time window.

### 4.8 Lifecycle Stage Detection

The lifecycle stage is determined by analyzing the composite score trajectory and growth rate:

| Stage | Criteria |
|-------|----------|
| **Emerging** | Low absolute volume, positive and accelerating growth |
| **Accelerating** | High growth rate, volume increasing rapidly |
| **Peak** | Volume near maximum, growth rate approaching zero |
| **Saturation** | Volume plateauing or slightly declining, growth rate near zero or slightly negative |
| **Decline** | Volume dropping, sustained negative growth |
| **Dormant** | Very low volume, minimal activity |

Logic: Use rolling growth rates over sub-windows within the selected period. Compare current growth rate to previous growth rate to detect acceleration/deceleration.

### 4.9 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | No | Register new user |
| POST | `/api/auth/login` | No | Login, receive JWT |
| GET | `/api/trends/top` | Yes | Get top 10 trends. Query params: `period` (7/14/30/60/90 days, default 7) |
| GET | `/api/trends/search` | Yes | Search a custom keyword. Query params: `keyword`, `period`. Triggers on-demand scrape if no recent data. |
| GET | `/api/trends/{keyword}/details` | Yes | Full detail for a keyword: time series, price, volume, volatility, region data, lifecycle |
| GET | `/api/trends/{keyword}/regions` | Yes | Region heatmap data. Query params: `scope` (`us` or `global`) |
| GET | `/api/keywords` | Yes | List all tracked keywords and their status |
| POST | `/api/keywords/{keyword}/activate` | Yes | Promote a `pending_review` keyword to `active` |

### 4.10 On-Demand Scraping Flow

When a user searches a custom keyword:

1. Check `trend_data` for recent data (< 6 hours old) for that keyword.
2. If fresh data exists → compute and return results immediately.
3. If no data or stale → trigger scraping for that keyword across all sources.
4. Insert raw data into `trend_data`, compute scores, and return results.
5. Add the keyword to `keywords` table with `source = 'user_search'` and `status = 'active'` so it gets picked up by scheduled jobs going forward.

---

## 5. Docker Compose

```yaml
version: "3.8"

services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - backend-data:/app/data    # Persist SQLite DB and CSV across restarts
    environment:
      - JWT_SECRET=<generate-a-secret>
      - REDDIT_CLIENT_ID=<your-reddit-client-id>
      - REDDIT_CLIENT_SECRET=<your-reddit-client-secret>

volumes:
  backend-data:
```

---

## 6. Project Directory Structure

```
cs667/
├── docs/
│   └── CREATE/
│       └── SYSTEM.md           # This file
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LoginForm.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── TrendCard.jsx
│   │   │   ├── TrendDetail.jsx
│   │   │   ├── SearchBar.jsx
│   │   │   ├── TimePeriodSelector.jsx
│   │   │   ├── RegionHeatmap.jsx
│   │   │   ├── LifecycleBadge.jsx
│   │   │   └── Charts/
│   │   │       ├── VolumeChart.jsx
│   │   │       ├── PriceChart.jsx
│   │   │       └── VolatilityChart.jsx
│   │   ├── services/
│   │   │   └── api.js          # Axios/fetch wrapper for API calls
│   │   ├── hooks/
│   │   │   └── useAuth.js      # Auth context and token management
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── nginx.conf
│   ├── package.json
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── database.py
│   │   ├── auth/
│   │   ├── trends/
│   │   ├── scrapers/
│   │   └── scheduler/
│   ├── data/
│   │   ├── trends.db
│   │   ├── users.csv
│   │   └── seed_keywords.json
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 7. Key Dependencies

### Frontend
- react, react-dom, react-router-dom
- axios (HTTP client)
- recharts or chart.js + react-chartjs-2 (charts)
- react-simple-maps or leaflet + react-leaflet (heatmaps)
- tailwindcss (optional, for responsive styling)

### Backend
- fastapi, uvicorn
- pandas (CSV user management)
- pytrends (Google Trends)
- praw (Reddit API)
- requests, beautifulsoup4 (web scraping for eBay, Depop)
- apscheduler (background job scheduling)
- python-jose (JWT tokens)
- passlib, bcrypt (password hashing)
- aiosqlite or sqlite3 (database)

---

## 8. Implementation Phases

### Phase 1 — Foundation
- [ ] Set up Docker Compose with frontend and backend containers
- [ ] Implement FastAPI skeleton with health check endpoint
- [ ] Set up React app with Vite, Nginx config, and routing
- [ ] Implement user auth (register/login with CSV + JWT)
- [ ] Set up SQLite database and tables

### Phase 2 — Data Pipeline
- [ ] Implement Google Trends scraper
- [ ] Implement eBay sold listings scraper
- [ ] Implement Reddit scraper
- [ ] Implement Depop scraper
- [ ] Set up APScheduler with scrape and score jobs
- [ ] Implement composite score calculation and lifecycle detection
- [ ] Seed keyword list and auto-discovery module

### Phase 3 — Dashboard
- [ ] Build landing page with login/registration form
- [ ] Build dashboard layout (controls bar + trend cards)
- [ ] Implement top 10 emerging trends view
- [ ] Build expanded trend detail view (charts, heatmap, lifecycle badge)
- [ ] Implement custom keyword search with on-demand scraping
- [ ] Implement time period selector
- [ ] Add region heatmap with US/global toggle
- [ ] Mobile-adaptive responsive design

### Phase 4 — Future Enhancements (TBD)
- [ ] Trend forecasting / prediction model
- [ ] (Additional features to be defined)

---

## 9. Notes & Constraints

- **Local-only for now**: No cloud deployment. Everything runs on Docker locally.
- **User auth is intentionally simple**: CSV-based storage with pandas. No OAuth, no email verification. This is a prototype.
- **Scraping fragility**: eBay and Depop scrapers depend on page structure and may break if those sites change their HTML. Build scrapers with error handling and fallback logic.
- **Rate limiting**: Google Trends and Reddit have rate limits. The scheduler should space out requests and handle 429 errors with exponential backoff.
- **Data freshness**: Scheduled scrapes every 6 hours. On-demand scrapes fill gaps for custom searches. Data older than 6 hours is considered stale for on-demand checks.
