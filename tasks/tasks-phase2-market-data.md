# Phase 2: Market Data Integration (Weeks 3-4)

## PRD Reference

**Source:** `/PRD.md`
**Key Requirements:**
- Integrate Twelve Data API for historical OHLCV data (1 year per stock)
- Implement real-time price streaming during market hours
- Build stock watchlist management (5-10 stocks max)
- Create data update scheduler for daily bar completion (4:05 PM ET)
- Implement rate limiting for API calls (8/minute, 800/day free tier)
- Add market hours detection logic

**Development Approach:** Implementation-first with manual testing, automated tests and documentation at end of cycle

## Relevant Files

### To Be Created:
- `backend/app/services/` - Services directory
- `backend/app/services/data/` - Market data services
- `backend/app/services/data/twelve_data_client.py` - Twelve Data API wrapper
- `backend/app/services/data/data_service.py` - Historical data fetching service
- `backend/app/services/data/realtime_service.py` - Real-time price streaming
- `backend/app/services/data/scheduler.py` - Data update scheduler
- `backend/app/services/data/market_hours.py` - Market hours utility
- `backend/app/api/endpoints/stocks.py` - Stock watchlist API
- `backend/app/api/endpoints/market_data.py` - Market data API
- `backend/app/schemas/` - Pydantic schemas directory
- `backend/app/schemas/stock.py` - Stock request/response schemas
- `backend/app/schemas/market_data.py` - Market data schemas
- `backend/app/core/rate_limiter.py` - API rate limiting utility

### Files to Modify:
- `backend/app/main.py` - Add new API routes
- `backend/app/models/stock.py` - May need relationship updates
- `backend/app/models/stock_data.py` - May need indexes

### Notes

- Focus on implementing data fetching that can be manually tested via API endpoints
- Use Postman or curl to verify data is stored correctly in database
- Test rate limiting by making rapid API calls
- Automated tests will be created at end of Phase 2

## Tasks

| Task |  #  | Status | Description                               |     | Dependencies | Pts | Time Spent |
| :--: | :-: | :----: | ----------------------------------------- | :-: | :----------: | :-: | :--------: |
|  1   |     |   -    | **Implement Twelve Data API Client**      | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create                                    | 🟢  |      -       |  3  |     -      |
|      |     |        | services/data/twelve_data_client.py       |     |              |     |            |
|      |     |        | with base HTTP client using httpx         |     |              |     |            |
|      |  2  |   -    | Implement get_time_series() method for    | 🟡  |     1.1      |  3  |     -      |
|      |     |        | historical OHLCV with params:             |     |              |     |            |
|      |     |        | symbol, interval, start/end dates         |     |              |     |            |
|      |  3  |   -    | Implement get_quote() method for          | 🟡  |     1.1      |  2  |     -      |
|      |     |        | real-time price with symbol param         |     |              |     |            |
|      |  4  |   -    | Add error handling for API errors         | 🟡  |     1.2-1.3  |  3  |     -      |
|      |     |        | (rate limits, invalid symbols,            |     |              |     |            |
|      |     |        | network issues)                           |     |              |     |            |
|      |  5  |   -    | Manually test API client by calling       | 🟡  |     1.4      |  1  |     -      |
|      |     |        | methods in Python shell with AAPL         |     |              |     |            |
|      |  6  |   -    | Implement response validation using       | 🟡  |     1.2-1.3  |  2  |     -      |
|      |     |        | Pydantic schemas                          |     |              |     |            |
|  2   |     |   -    | **Create Historical Data Fetching         | 🟢  |      -       |  -  |     -      |
|      |     |        | Service**                                 |     |              |     |            |
|      |  1  |   -    | Create core/rate_limiter.py with token    | 🟢  |      -       |  3  |     -      |
|      |     |        | bucket algorithm (8 calls/min, 800/day)   |     |              |     |            |
|      |  2  |   -    | Create services/data/data_service.py      | 🟢  |      1       |  5  |     -      |
|      |     |        | with fetch_historical_data() method       |     |              |     |            |
|      |     |        | that fetches 1 year daily bars            |     |              |     |            |
|      |  3  |   -    | Implement data storage logic: insert      | 🟡  |     2.2      |  3  |     -      |
|      |     |        | OHLCV records into stock_data table       |     |              |     |            |
|      |     |        | with conflict handling                    |     |              |     |            |
|      |  4  |   -    | Add rate limiter to data_service          | 🟡  |     2.1-2.2  |  2  |     -      |
|      |     |        | before API calls                          |     |              |     |            |
|      |  5  |   -    | Implement retry logic with exponential    | 🟡  |     2.2      |  3  |     -      |
|      |     |        | backoff (3 attempts, 1s/2s/4s delays)     |     |              |     |            |
|      |  6  |   -    | Add logging for successful fetches,       | 🟡  |     2.2      |  2  |     -      |
|      |     |        | errors, rate limit hits                   |     |              |     |            |
|      |  7  |   -    | Create API endpoint POST                  | 🟡  |     2.3      |  3  |     -      |
|      |     |        | /api/market-data/fetch-historical         |     |              |     |            |
|      |     |        | with params: symbol, start_date           |     |              |     |            |
|      |  8  |   -    | Manually test by fetching AAPL 1 year     | 🟡  |     2.7      |  2  |     -      |
|      |     |        | data via Postman and verify DB            |     |              |     |            |
|      |     |        | records                                   |     |              |     |            |
|  3   |     |   -    | **Build Stock Watchlist Management**      | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create schemas/stock.py with              | 🟢  |      -       |  2  |     -      |
|      |     |        | StockCreate, StockResponse schemas        |     |              |     |            |
|      |  2  |   -    | Create api/endpoints/stocks.py with       | 🟡  |     3.1      |  3  |     -      |
|      |     |        | CRUD endpoints: GET/POST/DELETE           |     |              |     |            |
|      |     |        | /api/stocks                               |     |              |     |            |
|      |  3  |   -    | Implement POST /api/stocks to add stock   | 🟡  |     3.2      |  3  |     -      |
|      |     |        | with validation (max 10 stocks limit)     |     |              |     |            |
|      |  4  |   -    | Implement GET /api/stocks to list all     | 🟡  |     3.2      |  2  |     -      |
|      |     |        | watchlist stocks                          |     |              |     |            |
|      |  5  |   -    | Implement DELETE /api/stocks/{symbol}     | 🟡  |     3.2      |  2  |     -      |
|      |     |        | to remove stock                           |     |              |     |            |
|      |  6  |   -    | Add symbol validation (check if exists    | 🟡  |     3.3      |  2  |     -      |
|      |     |        | on exchange via Twelve Data API)          |     |              |     |            |
|      |  7  |   -    | Manually test watchlist CRUD via          | 🟡  |     3.3-3.5  |  2  |     -      |
|      |     |        | Postman: add AAPL, MSFT, GOOGL,           |     |              |     |            |
|      |     |        | list, delete                              |     |              |     |            |
|      |  8  |   -    | Trigger historical data fetch when        | 🟡  |     2, 3.3   |  3  |     -      |
|      |     |        | stock added to watchlist (background      |     |              |     |            |
|      |     |        | task)                                     |     |              |     |            |
|  4   |     |   -    | **Implement Real-time Price Streaming**   | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create                                    | 🟢  |      1       |  3  |     -      |
|      |     |        | services/data/realtime_service.py         |     |              |     |            |
|      |     |        | with get_realtime_prices() for            |     |              |     |            |
|      |     |        | watchlist                                 |     |              |     |            |
|      |  2  |   -    | Implement polling approach: call          | 🟡  |     4.1      |  3  |     -      |
|      |     |        | Twelve Data REST API every 30             |     |              |     |            |
|      |     |        | seconds                                   |     |              |     |            |
|      |  3  |   -    | Add Redis caching for price data          | 🟡  |     4.2      |  3  |     -      |
|      |     |        | (TTL=30s) to reduce API calls             |     |              |     |            |
|      |  4  |   -    | Create WebSocket endpoint                 | 🟡  |     4.1      |  5  |     -      |
|      |     |        | /ws/prices that broadcasts updates        |     |              |     |            |
|      |     |        | to connected clients                      |     |              |     |            |
|      |  5  |   -    | Implement connection manager to track     | 🟡  |     4.4      |  3  |     -      |
|      |     |        | WebSocket clients                         |     |              |     |            |
|      |  6  |   -    | Start background task on app startup      | 🟡  |     4.2, 4.4 |  2  |     -      |
|      |     |        | to poll prices and broadcast via          |     |              |     |            |
|      |     |        | WebSocket                                 |     |              |     |            |
|      |  7  |   -    | Manually test WebSocket by connecting     | 🟡  |     4.6      |  2  |     -      |
|      |     |        | from browser console and receiving        |     |              |     |            |
|      |     |        | price updates                             |     |              |     |            |
|  5   |     |   -    | **Create Data Update Scheduler**          | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Choose scheduler: APScheduler             | 🟢  |      -       |  1  |     -      |
|      |     |        | (simpler) or Celery Beat (if using        |     |              |     |            |
|      |     |        | Celery)                                   |     |              |     |            |
|      |  2  |   -    | Install APScheduler and add to            | 🟡  |     5.1      |  1  |     -      |
|      |     |        | requirements.txt                          |     |              |     |            |
|      |  3  |   -    | Create services/data/scheduler.py with    | 🟡  |     5.2      |  5  |     -      |
|      |     |        | APScheduler instance and job              |     |              |     |            |
|      |     |        | definitions                               |     |              |     |            |
|      |  4  |   -    | Implement daily_bar_update_job() that     | 🟡  |     2, 5.3   |  3  |     -      |
|      |     |        | triggers at 4:05 PM ET: fetch latest      |     |              |     |            |
|      |     |        | daily bar for all watchlist stocks        |     |              |     |            |
|      |  5  |   -    | Add scheduler lifecycle management:       | 🟡  |     5.3      |  2  |     -      |
|      |     |        | start on app startup, shutdown on         |     |              |     |            |
|      |     |        | app stop                                  |     |              |     |            |
|      |  6  |   -    | Add logging for scheduled jobs:           | 🟡  |     5.4      |  1  |     -      |
|      |     |        | start, completion, errors                 |     |              |     |            |
|      |  7  |   -    | Create API endpoint GET                   | 🟡  |     5.5      |  2  |     -      |
|      |     |        | /api/scheduler/status to check            |     |              |     |            |
|      |     |        | scheduler health                          |     |              |     |            |
|      |  8  |   -    | Manually test by temporarily setting      | 🟡  |     5.7      |  2  |     -      |
|      |     |        | job to run every 1 minute and             |     |              |     |            |
|      |     |        | verifying logs                            |     |              |     |            |
|  6   |     |   -    | **Add Market Hours Detection**            | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create services/data/market_hours.py      | 🟢  |      -       |  3  |     -      |
|      |     |        | with is_market_open() function            |     |              |     |            |
|      |     |        | (9:30 AM - 4:00 PM ET weekdays)           |     |              |     |            |
|      |  2  |   -    | Install pytz library and add to           | 🟡  |     6.1      |  1  |     -      |
|      |     |        | requirements.txt for timezone             |     |              |     |            |
|      |     |        | handling                                  |     |              |     |            |
|      |  3  |   -    | Implement market holiday check using      | 🟡  |     6.1      |  3  |     -      |
|      |     |        | pandas-market-calendars library           |     |              |     |            |
|      |  4  |   -    | Add pre-market (4:00-9:30 AM) and         | 🟡  |     6.3      |  2  |     -      |
|      |     |        | after-hours (4:00-8:00 PM) detection      |     |              |     |            |
|      |  5  |   -    | Create API endpoint GET                   | 🟡  |     6.1      |  2  |     -      |
|      |     |        | /api/market/status returning              |     |              |     |            |
|      |     |        | open/closed + next open/close time        |     |              |     |            |
|      |  6  |   -    | Manually test market_hours.py by          | 🟡  |     6.5      |  1  |     -      |
|      |     |        | running during/outside market             |     |              |     |            |
|      |     |        | hours                                     |     |              |     |            |
|      |  7  |   -    | Add market hours guard to realtime        | 🟡  |     4, 6.1   |  2  |     -      |
|      |     |        | service: only stream prices during        |     |              |     |            |
|      |     |        | market hours                              |     |              |     |            |
|  7   |     |   -    | **Write Integration Tests for Market      | 🟢  |      -       |  -  |     -      |
|      |     |        | Data**                                    |     |              |     |            |
|      |  1  |   -    | Create tests/test_twelve_data_client.py   | 🟢  |      6       |  3  |     -      |
|      |     |        | with mocked API responses                 |     |              |     |            |
|      |  2  |   -    | Create tests/test_data_service.py for     | 🟡  |     7.1      |  5  |     -      |
|      |     |        | historical data fetch and storage         |     |              |     |            |
|      |  3  |   -    | Create tests/test_stocks_api.py for       | 🟡  |     7.1      |  3  |     -      |
|      |     |        | watchlist CRUD endpoints                  |     |              |     |            |
|      |  4  |   -    | Create tests/test_rate_limiter.py for     | 🟡  |     7.1      |  3  |     -      |
|      |     |        | rate limiting logic                       |     |              |     |            |
|      |  5  |   -    | Create tests/test_market_hours.py for     | 🟡  |     7.1      |  2  |     -      |
|      |     |        | market hours detection                    |     |              |     |            |
|      |  6  |   -    | Create tests/test_scheduler.py for        | 🟡  |     7.1      |  3  |     -      |
|      |     |        | scheduled job execution                   |     |              |     |            |
|      |  7  |   -    | Run pytest and ensure all Phase 2         | 🟡  |     7.2-7.6  |  1  |     -      |
|      |     |        | tests pass with 70%+ coverage             |     |              |     |            |
|  8   |     |   -    | **Document Market Data Integration**      | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Update README with Phase 2 setup:         | 🟢  |      7       |  2  |     -      |
|      |     |        | Twelve Data API key, testing data         |     |              |     |            |
|      |     |        | fetch                                     |     |              |     |            |
|      |  2  |   -    | Create docs/MARKET_DATA.md documenting    | 🟡  |     8.1      |  3  |     -      |
|      |     |        | API integration, rate limits,             |     |              |     |            |
|      |     |        | caching strategy                          |     |              |     |            |
|      |  3  |   -    | Document scheduler jobs and timing in     | 🟡  |     8.2      |  2  |     -      |
|      |     |        | MARKET_DATA.md                            |     |              |     |            |
|      |  4  |   -    | Add API endpoint documentation with       | 🟡  |     8.2      |  2  |     -      |
|      |     |        | examples for watchlist and data           |     |              |     |            |
|      |     |        | fetching                                  |     |              |     |            |
|      |  5  |   -    | Document troubleshooting: rate limit      | 🟡  |     8.4      |  2  |     -      |
|      |     |        | errors, missing data, API failures        |     |              |     |            |

---

**Phase 2 Total Sprint Points:** ~131 points
**Estimated Duration:** 2 weeks
**Key Deliverables:** Historical data fetching working, watchlist management, real-time price streaming, daily data scheduler, market hours detection, integration tests passing
