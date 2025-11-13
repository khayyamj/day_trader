# Phase 6: Frontend Dashboard (Weeks 11-12)

## PRD Reference

**Source:** `/PRD.md`
**Key Requirements:**
- Build single-page React dashboard for monitoring trading activity
- Implement candlestick chart with indicator overlays using Lightweight Charts
- Create synchronized volume chart below main chart
- Display current open positions with live P&L updates
- Show recent trades table (last 20 trades)
- Build strategy control panel (activate/pause, configure parameters)
- Implement WebSocket real-time updates (price, P&L, new trades, signals)
- Create alert/notification UI components for in-app messages
- Dashboard must load in <3 seconds, update prices every 5 seconds

**Development Approach:** Implementation-first with manual testing, automated tests and documentation at end of cycle

## Relevant Files

### To Be Created:
- `frontend/` - React application root
- `frontend/src/` - Source code directory
- `frontend/src/App.tsx` - Main application component
- `frontend/src/components/` - React components
- `frontend/src/components/layout/` - Layout components
- `frontend/src/components/layout/Dashboard.tsx` - Main dashboard layout
- `frontend/src/components/charts/` - Chart components
- `frontend/src/components/charts/CandlestickChart.tsx` - Main price chart using Lightweight Charts
- `frontend/src/components/charts/VolumeChart.tsx` - Volume bar chart using Recharts
- `frontend/src/components/charts/IndicatorOverlay.tsx` - EMA/RSI indicators on chart
- `frontend/src/components/tables/` - Table components
- `frontend/src/components/tables/PositionsTable.tsx` - Open positions display
- `frontend/src/components/tables/TradesTable.tsx` - Recent trades history
- `frontend/src/components/strategy/` - Strategy control components
- `frontend/src/components/strategy/StrategyPanel.tsx` - Strategy status and controls
- `frontend/src/components/strategy/StrategyConfig.tsx` - Parameter configuration modal
- `frontend/src/components/alerts/` - Alert components
- `frontend/src/components/alerts/AlertToast.tsx` - Toast notifications
- `frontend/src/components/alerts/AlertPanel.tsx` - Alert history panel
- `frontend/src/services/` - API services
- `frontend/src/services/api.ts` - REST API client (axios)
- `frontend/src/services/websocket.ts` - WebSocket client
- `frontend/src/hooks/` - Custom React hooks
- `frontend/src/hooks/useWebSocket.ts` - WebSocket connection hook
- `frontend/src/hooks/useRealTimeData.ts` - Real-time data hook
- `frontend/src/types/` - TypeScript types
- `frontend/src/types/index.ts` - Type definitions
- `frontend/package.json` - Dependencies

### Notes

- Focus on implementing UI components that display real data from backend
- Test with browser developer tools and React DevTools
- Verify WebSocket connections and real-time updates manually
- Test responsive layout at different screen sizes (1920x1080, 1366x768)
- Automated component tests will be created at end of Phase 6

## Tasks

| Task |  #  | Status | Description                               |     | Dependencies | Pts | Time Spent |
| :--: | :-: | :----: | ----------------------------------------- | :-: | :----------: | :-: | :--------: |
|  1   |     |   -    | **Set Up React Application**              | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Initialize React app with Vite (faster)   | 🟢  |      -       |  2  |     -      |
|      |     |        | or Create React App: `npm create          |     |              |     |            |
|      |     |        | vite@latest frontend --template           |     |              |     |            |
|      |     |        | react-ts`                                 |     |              |     |            |
|      |  2  |   -    | Install core dependencies: axios,         | 🟡  |     1.1      |  2  |     -      |
|      |     |        | lightweight-charts, recharts, date-fns    |     |              |     |            |
|      |  3  |   -    | Configure TypeScript with strict mode     | 🟡  |     1.1      |  1  |     -      |
|      |     |        | and path aliases                          |     |              |     |            |
|      |  4  |   -    | Set up Tailwind CSS for styling (or      | 🟡  |     1.1      |  2  |     -      |
|      |     |        | CSS-in-JS solution like styled-           |     |              |     |            |
|      |     |        | components)                               |     |              |     |            |
|      |  5  |   -    | Create frontend/.env with                 | 🟡  |     1.1      | 0.5 |     -      |
|      |     |        | VITE_API_URL=http://localhost:8000        |     |              |     |            |
|      |  6  |   -    | Configure proxy for API calls to avoid    | 🟡  |     1.5      |  1  |     -      |
|      |     |        | CORS issues in development                |     |              |     |            |
|      |  7  |   -    | Create basic App.tsx with routing         | 🟡  |     1.4      |  2  |     -      |
|      |     |        | (react-router-dom) - single route to      |     |              |     |            |
|      |     |        | dashboard                                 |     |              |     |            |
|      |  8  |   -    | Test app runs: npm run dev, verify        | 🟡  |     1.7      |  1  |     -      |
|      |     |        | opens in browser at localhost:5173        |     |              |     |            |
|  2   |     |   -    | **Build Dashboard Layout and              | 🟢  |      -       |  -  |     -      |
|      |     |        | Navigation**                              |     |              |     |            |
|      |  1  |   -    | Create types/index.ts with TypeScript     | 🟢  |      -       |  3  |     -      |
|      |     |        | interfaces: Position, Trade, Strategy,    |     |              |     |            |
|      |     |        | Signal, Alert                             |     |              |     |            |
|      |  2  |   -    | Create components/layout/Dashboard.tsx    | 🟡  |     2.1      |  5  |     -      |
|      |     |        | with grid layout: header, main chart      |     |              |     |            |
|      |     |        | area, side panel, bottom panel            |     |              |     |            |
|      |  3  |   -    | Create Header component with app title,   | 🟡  |     2.2      |  2  |     -      |
|      |     |        | portfolio value display, strategy         |     |              |     |            |
|      |     |        | status                                    |     |              |     |            |
|      |  4  |   -    | Create SidePanel component for strategy   | 🟡  |     2.2      |  3  |     -      |
|      |     |        | controls and positions table              |     |              |     |            |
|      |  5  |   -    | Create BottomPanel component for trades   | 🟡  |     2.2      |  3  |     -      |
|      |     |        | table and alerts                          |     |              |     |            |
|      |  6  |   -    | Implement responsive grid that adapts     | 🟡  |     2.2-2.5  |  3  |     -      |
|      |     |        | to screen size (1920x1080, 1366x768)      |     |              |     |            |
|      |  7  |   -    | Test layout in browser at different       | 🟡  |     2.6      |  1  |     -      |
|      |     |        | sizes, verify no overflow                 |     |              |     |            |
|  3   |     |   -    | **Implement Candlestick Chart             | 🟢  |      -       |  -  |     -      |
|      |     |        | Component**                               |     |              |     |            |
|      |  1  |   -    | Install lightweight-charts library:       | 🟢  |      -       |  1  |     -      |
|      |     |        | npm install lightweight-charts            |     |              |     |            |
|      |  2  |   -    | Create                                    | 🟡  |     3.1      |  8  |     -      |
|      |     |        | components/charts/CandlestickChart.tsx    |     |              |     |            |
|      |     |        | with chart initialization using           |     |              |     |            |
|      |     |        | createChart()                             |     |              |     |            |
|      |  3  |   -    | Implement data fetching: GET              | 🟡  |     3.2      |  3  |     -      |
|      |     |        | /api/market-data/ohlcv for selected       |     |              |     |            |
|      |     |        | stock                                     |     |              |     |            |
|      |  4  |   -    | Format data for Lightweight Charts:       | 🟡  |     3.3      |  2  |     -      |
|      |     |        | convert to {time, open, high, low,        |     |              |     |            |
|      |     |        | close}                                    |     |              |     |            |
|      |  5  |   -    | Add candlestick series to chart with      | 🟡  |     3.4      |  2  |     -      |
|      |     |        | styling (green up, red down)              |     |              |     |            |
|      |  6  |   -    | Implement chart controls: zoom,           | 🟡  |     3.5      |  3  |     -      |
|      |     |        | pan, crosshair                            |     |              |     |            |
|      |  7  |   -    | Add stock symbol selector dropdown to     | 🟡  |     3.2      |  2  |     -      |
|      |     |        | switch between watchlist stocks           |     |              |     |            |
|      |  8  |   -    | Test chart with real OHLCV data from      | 🟡  |     3.7      |  2  |     -      |
|      |     |        | backend, verify displays correctly        |     |              |     |            |
|  4   |     |   -    | **Build Volume and Indicator Charts**     | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Install recharts library: npm install     | 🟢  |      -       |  1  |     -      |
|      |     |        | recharts                                  |     |              |     |            |
|      |  2  |   -    | Create components/charts/VolumeChart.tsx  | 🟡  |     4.1      |  5  |     -      |
|      |     |        | using Recharts BarChart                   |     |              |     |            |
|      |  3  |   -    | Synchronize volume chart timeline with    | 🟡  |     3, 4.2   |  3  |     -      |
|      |     |        | main candlestick chart (shared X-axis)    |     |              |     |            |
|      |  4  |   -    | Color volume bars: green on up days,      | 🟡  |     4.2      |  2  |     -      |
|      |     |        | red on down days                          |     |              |     |            |
|      |  5  |   -    | Create                                    | 🟡  |     3        |  5  |     -      |
|      |     |        | components/charts/IndicatorOverlay.tsx    |     |              |     |            |
|      |     |        | to add EMA lines to main chart            |     |              |     |            |
|      |  6  |   -    | Fetch indicator data: GET                 | 🟡  |     4.5      |  2  |     -      |
|      |     |        | /api/indicators/calculate with EMA(20),   |     |              |     |            |
|      |     |        | EMA(50)                                   |     |              |     |            |
|      |  7  |   -    | Add EMA(20) line series to chart (blue)   | 🟡  |     4.6      |  2  |     -      |
|      |  8  |   -    | Add EMA(50) line series to chart          | 🟡  |     4.7      |  2  |     -      |
|      |     |        | (orange)                                  |     |              |     |            |
|      |  9  |   -    | Add buy/sell signal markers on chart      | 🟡  |     4.5      |  3  |     -      |
|      |     |        | (arrows or triangles)                     |     |              |     |            |
|      | 10  |   -    | Test charts with indicators and signals,  | 🟡  |     4.9      |  2  |     -      |
|      |     |        | verify overlays display correctly         |     |              |     |            |
|  5   |     |   -    | **Create Positions and Trades Tables**    | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create                                    | 🟢  |      -       |  5  |     -      |
|      |     |        | components/tables/PositionsTable.tsx      |     |              |     |            |
|      |     |        | with columns: Symbol, Qty, Entry, Curr,   |     |              |     |            |
|      |     |        | P&L, P&L%                                 |     |              |     |            |
|      |  2  |   -    | Fetch positions data: GET /api/positions  | 🟡  |     5.1      |  2  |     -      |
|      |  3  |   -    | Calculate live P&L: (current_price -      | 🟡  |     5.2      |  3  |     -      |
|      |     |        | entry_price) * quantity                   |     |              |     |            |
|      |  4  |   -    | Color code P&L: green for profit, red     | 🟡  |     5.3      |  1  |     -      |
|      |     |        | for loss                                  |     |              |     |            |
|      |  5  |   -    | Add expand/collapse for position details  | 🟡  |     5.1      |  3  |     -      |
|      |     |        | (stop-loss, take-profit, entry reason)    |     |              |     |            |
|      |  6  |   -    | Create components/tables/TradesTable.tsx  | 🟡  |     5.1      |  5  |     -      |
|      |     |        | with columns: Symbol, Type, Entry/Exit,   |     |              |     |            |
|      |     |        | Time, P&L                                 |     |              |     |            |
|      |  7  |   -    | Fetch trades data: GET /api/trades with   | 🟡  |     5.6      |  2  |     -      |
|      |     |        | limit=20, sort by timestamp desc          |     |              |     |            |
|      |  8  |   -    | Add pagination or infinite scroll for     | 🟡  |     5.6      |  3  |     -      |
|      |     |        | viewing older trades                      |     |              |     |            |
|      |  9  |   -    | Test tables with real data from backend,  | 🟡  |     5.7-5.8  |  2  |     -      |
|      |     |        | verify displays correctly                 |     |              |     |            |
|  6   |     |   -    | **Implement Strategy Control Panel**      | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create                                    | 🟢  |      -       |  5  |     -      |
|      |     |        | components/strategy/StrategyPanel.tsx     |     |              |     |            |
|      |     |        | showing strategy status, consecutive      |     |              |     |            |
|      |     |        | losses, warm-up status                    |     |              |     |            |
|      |  2  |   -    | Fetch strategy data: GET /api/strategies  | 🟡  |     6.1      |  2  |     -      |
|      |  3  |   -    | Display strategy status badge: Active     | 🟡  |     6.2      |  2  |     -      |
|      |     |        | (green), Paused (yellow), Error (red),    |     |              |     |            |
|      |     |        | Warming (blue)                            |     |              |     |            |
|      |  4  |   -    | Add Activate/Pause buttons that call      | 🟡  |     6.2      |  3  |     -      |
|      |     |        | POST /api/strategies/{id}/activate or     |     |              |     |            |
|      |     |        | /pause                                    |     |              |     |            |
|      |  5  |   -    | Add Configure button that opens modal     | 🟡  |     6.4      |  2  |     -      |
|      |     |        | for parameter editing                     |     |              |     |            |
|      |  6  |   -    | Create                                    | 🟡  |     6.5      |  5  |     -      |
|      |     |        | components/strategy/StrategyConfig.tsx    |     |              |     |            |
|      |     |        | modal with form inputs for EMA            |     |              |     |            |
|      |     |        | periods, RSI threshold, stop-loss %       |     |              |     |            |
|      |  7  |   -    | Implement form validation: EMA periods    | 🟡  |     6.6      |  2  |     -      |
|      |     |        | 2-200, RSI 2-50, percentages 0-100        |     |              |     |            |
|      |  8  |   -    | Submit config changes: PUT                | 🟡  |     6.6      |  2  |     -      |
|      |     |        | /api/strategies/{id}/parameters           |     |              |     |            |
|      |  9  |   -    | Test strategy controls: activate,         | 🟡  |     6.4-6.8  |  2  |     -      |
|      |     |        | pause, update config, verify changes      |     |              |     |            |
|      |     |        | persist                                   |     |              |     |            |
|  7   |     |   -    | **Add WebSocket Real-time Updates**       | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create services/websocket.ts with         | 🟢  |      -       |  5  |     -      |
|      |     |        | WebSocketClient class                     |     |              |     |            |
|      |  2  |   -    | Implement connect() to                    | 🟡  |     7.1      |  3  |     -      |
|      |     |        | ws://localhost:8000/ws/prices             |     |              |     |            |
|      |  3  |   -    | Implement message handler: parse JSON     | 🟡  |     7.2      |  3  |     -      |
|      |     |        | messages, emit events for different       |     |              |     |            |
|      |     |        | message types                             |     |              |     |            |
|      |  4  |   -    | Add reconnection logic with exponential   | 🟡  |     7.2      |  3  |     -      |
|      |     |        | backoff (1s, 2s, 4s, 8s)                  |     |              |     |            |
|      |  5  |   -    | Create hooks/useWebSocket.ts custom hook  | 🟡  |     7.1      |  3  |     -      |
|      |     |        | for managing WebSocket connection         |     |              |     |            |
|      |  6  |   -    | Create hooks/useRealTimeData.ts that      | 🟡  |     7.5      |  5  |     -      |
|      |     |        | subscribes to price updates and           |     |              |     |            |
|      |     |        | manages state                             |     |              |     |            |
|      |  7  |   -    | Update PositionsTable to use real-time    | 🟡  |     5, 7.6   |  3  |     -      |
|      |     |        | prices for P&L calculations               |     |              |     |            |
|      |  8  |   -    | Update CandlestickChart to receive live   | 🟡  |     3, 7.6   |  3  |     -      |
|      |     |        | price updates and append to chart         |     |              |     |            |
|      |  9  |   -    | Test WebSocket: connect, receive price    | 🟡  |     7.8      |  2  |     -      |
|      |     |        | updates, verify tables/charts update      |     |              |     |            |
|      |     |        | in real-time                              |     |              |     |            |
|  8   |     |   -    | **Implement Alert/Notification UI**       | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create components/alerts/AlertToast.tsx   | 🟢  |      -       |  3  |     -      |
|      |     |        | for toast notifications (library:         |     |              |     |            |
|      |     |        | react-hot-toast)                          |     |              |     |            |
|      |  2  |   -    | Install react-hot-toast: npm install      | 🟡  |     8.1      |  1  |     -      |
|      |     |        | react-hot-toast                           |     |              |     |            |
|      |  3  |   -    | Create AlertContext for global alert      | 🟡  |     8.1      |  3  |     -      |
|      |     |        | management with show/hide methods         |     |              |     |            |
|      |  4  |   -    | Implement alert types: info (blue),       | 🟡  |     8.3      |  2  |     -      |
|      |     |        | warning (yellow), error (red), success    |     |              |     |            |
|      |     |        | (green)                                   |     |              |     |            |
|      |  5  |   -    | Create components/alerts/AlertPanel.tsx   | 🟡  |     8.3      |  3  |     -      |
|      |     |        | showing recent alerts (last 20)           |     |              |     |            |
|      |  6  |   -    | Fetch alerts from WebSocket: listen for   | 🟡  |     7, 8.5   |  3  |     -      |
|      |     |        | 'alert' message type                      |     |              |     |            |
|      |  7  |   -    | Show toast for: trade execution, signal   | 🟡  |     8.6      |  2  |     -      |
|      |     |        | generated, risk limit warning, errors     |     |              |     |            |
|      |  8  |   -    | Test alerts: manually trigger events in   | 🟡  |     8.7      |  2  |     -      |
|      |     |        | backend, verify toasts display            |     |              |     |            |
|  9   |     |   -    | **Polish UI/UX and Error Handling**       | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Add loading states: spinner while         | 🟢  |      8       |  3  |     -      |
|      |     |        | fetching data, skeleton screens           |     |              |     |            |
|      |  2  |   -    | Add error boundaries to catch React       | 🟡  |     9.1      |  2  |     -      |
|      |     |        | errors and display fallback UI            |     |              |     |            |
|      |  3  |   -    | Implement retry logic for failed API      | 🟡  |     9.2      |  3  |     -      |
|      |     |        | calls with user feedback                  |     |              |     |            |
|      |  4  |   -    | Add empty states: "No positions", "No     | 🟡  |     9.1      |  2  |     -      |
|      |     |        | trades yet", "Add stocks to watchlist"    |     |              |     |            |
|      |  5  |   -    | Implement responsive design: test on      | 🟡  |     2, 9.1   |  3  |     -      |
|      |     |        | 1920x1080 and 1366x768, adjust            |     |              |     |            |
|      |     |        | layouts                                   |     |              |     |            |
|      |  6  |   -    | Add keyboard shortcuts: 'r' to refresh,   | 🟡  |     9.5      |  2  |     -      |
|      |     |        | 'p' to pause strategy                     |     |              |     |            |
|      |  7  |   -    | Optimize performance: memoize components, | 🟡  |     9.1      |  3  |     -      |
|      |     |        | debounce updates, lazy load charts        |     |              |     |            |
|      |  8  |   -    | Test dashboard load time: measure with    | 🟡  |     9.7      |  1  |     -      |
|      |     |        | DevTools, ensure <3 seconds               |     |              |     |            |
| 10   |     |   -    | **Write Component Tests**                 | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Set up Jest and React Testing Library:   | 🟢  |      9       |  2  |     -      |
|      |     |        | npm install -D @testing-library/react     |     |              |     |            |
|      |     |        | jest                                      |     |              |     |            |
|      |  2  |   -    | Create tests/CandlestickChart.test.tsx    | 🟡  |     10.1     |  3  |     -      |
|      |     |        | testing chart rendering                   |     |              |     |            |
|      |  3  |   -    | Create tests/PositionsTable.test.tsx      | 🟡  |     10.1     |  3  |     -      |
|      |     |        | testing table rendering and P&L           |     |              |     |            |
|      |     |        | calculation                               |     |              |     |            |
|      |  4  |   -    | Create tests/StrategyPanel.test.tsx       | 🟡  |     10.1     |  3  |     -      |
|      |     |        | testing button clicks and status          |     |              |     |            |
|      |     |        | display                                   |     |              |     |            |
|      |  5  |   -    | Create tests/useWebSocket.test.ts testing | 🟡  |     10.1     |  3  |     -      |
|      |     |        | WebSocket hook logic                      |     |              |     |            |
|      |  6  |   -    | Run npm test and ensure all component    | 🟡  |     10.2-10.5|  1  |     -      |
|      |     |        | tests pass                                |     |              |     |            |
| 11   |     |   -    | **Document Frontend Architecture**        | 🟢  |      -       |  -  |     -      |
|      |  1  |   -    | Create frontend/README.md with setup      | 🟢  |      10      |  2  |     -      |
|      |     |        | instructions, available scripts           |     |              |     |            |
|      |  2  |   -    | Document component structure and          | 🟡  |     11.1     |  3  |     -      |
|      |     |        | organization                              |     |              |     |            |
|      |  3  |   -    | Document WebSocket message format and     | 🟡  |     11.2     |  2  |     -      |
|      |     |        | event types                               |     |              |     |            |
|      |  4  |   -    | Document API service methods and usage    | 🟡  |     11.2     |  2  |     -      |
|      |  5  |   -    | Add screenshots of dashboard to docs      | 🟡  |     11.4     |  1  |     -      |

---

**Phase 6 Total Sprint Points:** ~183 points
**Estimated Duration:** 2 weeks
**Key Deliverables:** React dashboard fully functional, candlestick and volume charts displaying data, positions and trades tables with real-time updates, strategy control panel working, WebSocket real-time updates, alert notifications, responsive UI, component tests passing
