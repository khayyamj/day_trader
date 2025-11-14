# Market Data Integration

This document describes the market data integration implemented in Phase 2.

## Overview

The trading application integrates with Twelve Data API to fetch historical and real-time market data for stocks in the watchlist.

## Architecture

```
┌──────────────────┐
│  Watchlist API   │ ← Add/remove stocks
└────────┬─────────┘
         │
         ↓
┌──────────────────────────────────────────┐
│         Data Services                    │
├──────────────────────────────────────────┤
│  • Historical Data Fetching (on-demand)  │
│  • Real-time Price Streaming (30s poll)  │
│  • Daily Bar Updates (4:05 PM ET)        │
└────────┬─────────────────────────────────┘
         │
         ↓
┌────────────────────┐      ┌──────────────┐
│  Twelve Data API   │      │  PostgreSQL  │
│  (Rate Limited)    │      │  stock_data  │
└────────────────────┘      └──────────────┘
```

## Components

### 1. Twelve Data API Client

**File:** `app/services/data/twelve_data_client.py`

Wrapper around Twelve Data REST API with:
- HTTP client using `httpx`
- Error handling (rate limits, invalid symbols, network errors)
- Custom exceptions: `RateLimitError`, `InvalidSymbolError`
- Request logging

**Methods:**
- `get_time_series()` - Historical OHLCV data
- `get_quote()` - Real-time price quote
- `get_stock_info()` - Symbol validation and metadata

**Configuration:**
- API key from environment: `TWELVE_DATA_API_KEY`
- Base URL: `https://api.twelvedata.com`
- Timeout: 30 seconds

### 2. Rate Limiter

**File:** `app/core/rate_limiter.py`

Token bucket algorithm for API rate limiting:

**Limits (Free Tier):**
- 8 API calls per minute
- 800 API calls per day

**Features:**
- Automatic token refill
- Both sync and async methods
- Hard limit on daily calls
- Status reporting
- Blocking/non-blocking modes

**Usage:**
```python
from app.core.rate_limiter import twelve_data_limiter

# Sync
if twelve_data_limiter.acquire(wait=True):
    # Make API call

# Async
if await twelve_data_limiter.acquire_async(wait=True):
    # Make API call
```

### 3. Historical Data Service

**File:** `app/services/data/data_service.py`

Fetches and stores historical OHLCV data:

**Features:**
- Fetches 1 year of daily bars by default
- Stores in `stock_data` table
- Duplicate detection (skips existing timestamps)
- Retry logic: 3 attempts with exponential backoff (1s, 2s, 4s)
- Rate limiter integration
- Comprehensive logging

**Workflow:**
1. Validate stock exists in watchlist
2. Acquire rate limit token
3. Fetch data from Twelve Data API
4. Parse and validate OHLCV bars
5. Insert into database (skip duplicates)
6. Return statistics

**API Endpoint:**
```
POST /api/market-data/fetch-historical
{
    "symbol": "AAPL",
    "start_date": "2024-01-01",  // Optional
    "end_date": "2024-12-31"      // Optional
}
```

### 4. Real-time Price Streaming

**File:** `app/services/data/realtime_service.py`

Polls prices and broadcasts via WebSocket:

**Features:**
- Polling interval: 30 seconds
- In-memory cache (30s TTL)
- Broadcasts to all connected clients
- Connection manager tracks WebSocket clients
- Rate-limit aware (uses cache if limit hit)

**WebSocket Endpoint:**
```
ws://localhost:8000/ws/prices
```

**Message Format:**
```json
{
    "type": "price_update",
    "timestamp": "2025-01-15T12:00:00",
    "prices": {
        "AAPL": {
            "symbol": "AAPL",
            "close": "150.25",
            "open": "149.50",
            "high": "151.00",
            "low": "149.00",
            "volume": "50000000",
            "change": "0.75",
            "percent_change": "0.50"
        }
    }
}
```

**Browser Testing:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/prices');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
ws.send('ping');  // Keepalive
```

### 5. Data Update Scheduler

**File:** `app/services/data/scheduler.py`

APScheduler for automated data updates:

**Jobs:**
- **Daily Bar Update**: Runs at 4:05 PM ET daily
  - Fetches last 2 days of data for all watchlist stocks
  - Ensures latest completed bar is captured
  - Comprehensive logging with summaries

**API Endpoints:**
```
GET /api/scheduler/status
POST /api/scheduler/trigger/daily_bar_update
```

**Manual Testing:**
```bash
# Trigger daily update immediately
curl -X POST http://localhost:8000/api/scheduler/trigger/daily_bar_update

# Check scheduler status
curl http://localhost:8000/api/scheduler/status
```

### 6. Market Hours Detection

**File:** `app/services/data/market_hours.py`

Determines US stock market trading status:

**Functions:**
- `is_market_open()` - Regular hours (9:30 AM - 4:00 PM ET)
- `is_pre_market()` - Pre-market (4:00 AM - 9:30 AM ET)
- `is_after_hours()` - Extended hours (4:00 PM - 8:00 PM ET)
- `is_market_holiday()` - US federal holidays 2025
- `get_market_status()` - Comprehensive status
- `get_next_market_times()` - Next open/close predictions

**Market Sessions:**
| Session | Hours (ET) | Description |
|---------|------------|-------------|
| Pre-market | 4:00 AM - 9:30 AM | Limited trading |
| Regular | 9:30 AM - 4:00 PM | Full trading day |
| After-hours | 4:00 PM - 8:00 PM | Extended trading |
| Closed | All other times | Weekends, holidays, nights |

**API Endpoint:**
```
GET /api/market/status
```

**Response:**
```json
{
    "current_time_et": "2025-01-15T14:30:00-05:00",
    "is_weekday": true,
    "is_holiday": false,
    "is_market_open": true,
    "is_pre_market": false,
    "is_after_hours": false,
    "session": "regular",
    "next_open": "2025-01-15T09:30:00-05:00",
    "next_close": "2025-01-15T16:00:00-05:00"
}
```

## API Endpoints Summary

### Watchlist Management

```bash
# List all stocks
GET /api/stocks/

# Add stock (triggers historical data fetch in background)
POST /api/stocks/
{
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NASDAQ"
}

# Get stock details
GET /api/stocks/{symbol}

# Remove stock
DELETE /api/stocks/{symbol}
```

### Market Data

```bash
# Fetch historical data
POST /api/market-data/fetch-historical
{
    "symbol": "AAPL",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
}
```

### Market Status

```bash
# Get current market status
GET /api/market/status
```

### Scheduler

```bash
# Get scheduler status
GET /api/scheduler/status

# Manually trigger daily update
POST /api/scheduler/trigger/daily_bar_update
```

## Rate Limiting

### Twelve Data Free Tier Limits

- **8 API calls per minute**
- **800 API calls per day**

### Rate Limiter Strategy

**Token Bucket Algorithm:**
- Tokens refill automatically over time
- Requests block/wait when tokens depleted
- Daily limit is hard (raises error when exceeded)

**Protection Mechanisms:**
1. Rate limiter checks before every API call
2. In-memory cache reduces API calls (30s TTL)
3. Background tasks respect limits
4. Graceful degradation (use cached data)

**Monitoring:**
```python
from app.core.rate_limiter import twelve_data_limiter

status = twelve_data_limiter.get_status()
# Returns: tokens_remaining_minute, tokens_remaining_day, reset times
```

## Data Storage

### Database Schema

**stock_data table:**
- `stock_id` - Foreign key to stocks table
- `timestamp` - Bar datetime (indexed)
- `open_price`, `high_price`, `low_price`, `close_price` - OHLCV data
- `volume` - Trading volume
- `created_at`, `updated_at` - Metadata

**Indexes:**
- `stock_id` - For filtering by stock
- `timestamp` - For time-range queries
- Composite index for efficient queries

### Conflict Handling

Duplicate timestamps are automatically skipped during insertion to prevent errors.

## Caching Strategy

### Real-time Prices (In-Memory Cache)

- **TTL:** 30 seconds
- **Purpose:** Reduce API calls for frequently requested data
- **Implementation:** Python dictionary with timestamp tracking
- **Eviction:** Automatic on TTL expiry

**Cache Flow:**
1. Check cache for symbol
2. If cached and < 30s old, return cached data
3. Otherwise, fetch from API
4. Update cache with new data

## Background Tasks

### 1. Historical Data Fetch (On-Demand)

**Trigger:** When stock added to watchlist
**Execution:** FastAPI BackgroundTasks
**Action:** Fetch 1 year of daily bars
**Status:** Fire-and-forget, logged

### 2. Daily Bar Update (Scheduled)

**Trigger:** 4:05 PM ET daily (after market close)
**Execution:** APScheduler cron job
**Action:** Fetch last 2 days for all watchlist stocks
**Status:** Logged with summary report

### 3. Real-time Price Streaming (Continuous)

**Trigger:** App startup (when enabled)
**Execution:** Asyncio background task
**Action:** Poll prices every 30s, broadcast via WebSocket
**Status:** Currently disabled, can be enabled in main.py

## Testing the Integration

### 1. Add a Stock to Watchlist

```bash
curl -X POST http://localhost:8000/api/stocks/ \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'
```

**Expected:**
- Stock added to database
- Background task queued for historical data fetch
- Returns stock details

### 2. Check Historical Data

```bash
# Via database
docker exec -it trading_postgres psql -U trading_user -d trading_db
SELECT COUNT(*) FROM stock_data WHERE stock_id = 1;
SELECT * FROM stock_data ORDER BY timestamp DESC LIMIT 10;
```

### 3. Fetch More Historical Data

```bash
curl -X POST http://localhost:8000/api/market-data/fetch-historical \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "start_date": "2023-01-01"}'
```

### 4. Check Market Status

```bash
curl http://localhost:8000/api/market/status
```

### 5. Test Scheduler

```bash
# View scheduler status
curl http://localhost:8000/api/scheduler/status

# Manually trigger daily update
curl -X POST http://localhost:8000/api/scheduler/trigger/daily_bar_update
```

### 6. Test WebSocket

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws/prices');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Price update:', data);
};
ws.onopen = () => console.log('Connected');
ws.onerror = (error) => console.error('WebSocket error:', error);
```

## Error Handling

### Rate Limit Exceeded

**HTTP 503:** Market data service unavailable
**Action:** Wait and retry, or use cached data

### Invalid Symbol

**HTTP 404:** Symbol not found
**Action:** Check symbol spelling, verify it exists on exchange

### API Key Missing/Invalid

**ValueError:** Twelve Data API key is required
**Action:** Set `TWELVE_DATA_API_KEY` in `.env` file

### Watchlist Limit

**HTTP 400:** Watchlist limit reached
**Action:** Remove unused stocks (max 10)

### Network Errors

**HTTP 503:** Service unavailable
**Action:** Automatic retry with exponential backoff

## Troubleshooting

### No Data Being Fetched

1. **Check API key:**
   ```bash
   # In backend directory
   source venv/bin/activate
   python -c "from app.core.config import settings; print(settings.TWELVE_DATA_API_KEY)"
   ```

2. **Check rate limiter:**
   ```bash
   curl http://localhost:8000/api/scheduler/status
   ```

3. **Check logs:**
   ```bash
   tail -f logs/trading_app.log | grep -i "twelve_data\|rate"
   ```

### Scheduler Not Running

1. **Check scheduler status:**
   ```bash
   curl http://localhost:8000/api/scheduler/status
   ```

2. **Manually trigger job:**
   ```bash
   curl -X POST http://localhost:8000/api/scheduler/trigger/daily_bar_update
   ```

3. **Check logs:**
   ```bash
   tail -f logs/trading_app.log | grep -i scheduler
   ```

### WebSocket Not Receiving Updates

1. **Enable price streaming** in `app/main.py` (uncomment lifespan code)
2. **Check connection:**
   ```javascript
   ws.readyState === WebSocket.OPEN  // Should be true
   ```
3. **Send ping:**
   ```javascript
   ws.send('ping');  // Should receive 'pong'
   ```

### Rate Limit Errors

**Free tier limits:** 8/minute, 800/day

**If exceeded:**
- Wait for minute reset
- Check status: `twelve_data_limiter.get_status()`
- Review logs for excessive API calls
- Consider upgrading Twelve Data plan

## Performance Optimization

### Caching

- **Real-time prices:** 30-second in-memory cache
- **Reduces API calls:** ~66% reduction for active monitoring
- **Trade-off:** Data may be up to 30s stale

### Background Fetching

- Historical data fetched asynchronously
- Doesn't block API responses
- User gets immediate feedback

### Database Indexing

- `stock_id` + `timestamp` indexed
- Fast time-range queries
- Efficient aggregations for indicators

## Next Steps (Phase 3)

With market data infrastructure complete, Phase 3 will implement:

1. **Technical Indicators:**
   - MACD calculation
   - RSI calculation
   - Moving averages (SMA, EMA)
   - Store in `indicators` table

2. **Signal Generation:**
   - MACD/RSI crossover logic
   - Buy/sell signal creation
   - Signal validation rules

3. **Strategy Engine:**
   - Strategy execution loop
   - Position management
   - Risk management rules

## References

- Twelve Data API Docs: https://twelvedata.com/docs
- APScheduler Docs: https://apscheduler.readthedocs.io/
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
