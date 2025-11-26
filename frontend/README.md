# Trading Dashboard Frontend

A real-time trading dashboard built with React, TypeScript, and Vite for monitoring algorithmic trading strategies.

## Features

- **Real-time Price Charts**: Interactive candlestick charts with technical indicators (EMA, RSI)
- **Live Position Tracking**: Monitor open positions with live P&L calculations
- **Trade History**: View recent trades with detailed execution information
- **Strategy Controls**: Activate/pause strategies and configure parameters
- **WebSocket Updates**: Real-time price and trade updates via WebSocket
- **Alert Notifications**: Toast notifications for trades, signals, and errors
- **Responsive Design**: Optimized for desktop viewing (1920x1080, 1366x768)

## Technology Stack

- **React 19** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS v4** - Styling
- **Lightweight Charts** - Professional candlestick charts
- **Recharts** - Volume charts
- **React Router** - Navigation
- **Axios** - HTTP client
- **React Hot Toast** - Notifications
- **Vitest** - Testing framework

## Prerequisites

- Node.js 18 or higher
- npm 9 or higher
- Backend API running on http://localhost:8000

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

The application will be available at http://localhost:5173

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build production bundle
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run test` - Run tests in watch mode
- `npm run test:ui` - Run tests with UI
- `npm run test:run` - Run tests once

## Project Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── alerts/          # Alert and notification components
│   │   │   ├── AlertPanel.tsx
│   │   │   └── AlertToast.tsx
│   │   ├── charts/          # Chart components
│   │   │   ├── CandlestickChart.tsx
│   │   │   ├── IndicatorOverlay.tsx
│   │   │   └── VolumeChart.tsx
│   │   ├── layout/          # Layout components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── SidePanel.tsx
│   │   │   └── BottomPanel.tsx
│   │   ├── strategy/        # Strategy control components
│   │   │   ├── StrategyPanel.tsx
│   │   │   └── StrategyConfig.tsx
│   │   └── tables/          # Table components
│   │       ├── PositionsTable.tsx
│   │       └── TradesTable.tsx
│   ├── hooks/               # Custom React hooks
│   │   ├── useWebSocket.ts
│   │   ├── useRealTimeData.ts
│   │   └── useKeyboardShortcuts.ts
│   ├── services/            # API and WebSocket services
│   │   ├── api.ts
│   │   └── websocket.ts
│   ├── types/               # TypeScript type definitions
│   │   └── index.ts
│   ├── test/                # Test setup
│   │   └── setup.ts
│   ├── App.tsx              # Main application component
│   └── main.tsx             # Application entry point
├── public/                  # Static assets
├── package.json
├── tsconfig.json            # TypeScript configuration
├── vite.config.ts           # Vite configuration
├── vitest.config.ts         # Vitest configuration
└── tailwind.config.js       # Tailwind CSS configuration
```

## Component Architecture

### Layout Components

- **Dashboard**: Main layout with grid for charts, positions, and controls
- **Header**: Application title, portfolio value, and strategy status
- **SidePanel**: Strategy controls and positions table
- **BottomPanel**: Trades table and alerts

### Chart Components

- **CandlestickChart**: Main price chart with OHLCV data using Lightweight Charts
- **VolumeChart**: Synchronized volume bars using Recharts
- **IndicatorOverlay**: EMA and signal overlays on the chart

### Table Components

- **PositionsTable**: Open positions with live P&L, expandable details
- **TradesTable**: Recent trade history with pagination

### Strategy Components

- **StrategyPanel**: Strategy status, consecutive losses, and control buttons
- **StrategyConfig**: Modal for editing strategy parameters

### Alert Components

- **AlertToast**: Toast notifications for real-time events
- **AlertPanel**: Alert history panel

## API Integration

The frontend communicates with the backend via REST API and WebSocket:

### REST API Endpoints

- `GET /api/market-data/ohlcv` - Fetch OHLCV data for charts
- `GET /api/indicators/calculate` - Fetch technical indicators
- `GET /api/signals/recent` - Fetch recent trading signals
- `GET /api/positions` - Fetch open positions
- `GET /api/trades` - Fetch trade history
- `GET /api/strategies` - Fetch strategy information
- `POST /api/strategies/{id}/activate` - Activate strategy
- `POST /api/strategies/{id}/pause` - Pause strategy
- `PUT /api/strategies/{id}/parameters` - Update strategy parameters

### WebSocket Connection

- **URL**: `ws://localhost:8000/ws/prices`
- **Messages**: Real-time price updates, trade executions, signals, and alerts

## WebSocket Message Format

### Price Update Message

```json
{
  "type": "price_update",
  "data": {
    "symbol": "AAPL",
    "price": 150.25,
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### Trade Execution Message

```json
{
  "type": "trade_execution",
  "data": {
    "symbol": "AAPL",
    "side": "buy",
    "price": 150.25,
    "quantity": 10,
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### Signal Generated Message

```json
{
  "type": "signal",
  "data": {
    "symbol": "AAPL",
    "signal_type": "buy",
    "price": 150.25,
    "confidence": 0.85,
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

### Alert Message

```json
{
  "type": "alert",
  "data": {
    "severity": "warning",
    "message": "Risk limit exceeded",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

## Custom Hooks

### useWebSocket

Manages WebSocket connection lifecycle and reconnection logic.

```typescript
const { isConnected, error, client } = useWebSocket();
```

### useRealTimeData

Subscribes to real-time price updates and manages state.

```typescript
const { getPrice, prices } = useRealTimeData();
```

### useKeyboardShortcuts

Handles keyboard shortcuts for quick actions.

```typescript
useKeyboardShortcuts({
  'r': refreshData,
  'p': pauseStrategy,
});
```

## Testing

The project uses Vitest and React Testing Library for testing.

### Running Tests

```bash
# Run tests in watch mode
npm run test

# Run tests once
npm run test:run

# Run tests with UI
npm run test:ui
```

### Test Coverage

- **CandlestickChart**: 8 tests
- **PositionsTable**: 12 tests
- **StrategyPanel**: 18 tests
- **useWebSocket**: 9 tests
- **Total**: 47 tests passing

## Performance Optimization

- Component memoization for expensive renders
- Debounced updates for real-time data (5 second intervals)
- Lazy loading for chart libraries
- Efficient WebSocket message handling
- Dashboard load time: <3 seconds

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development Guidelines

### Code Style

- Follow TypeScript strict mode
- Use functional components with hooks
- Prefer composition over inheritance
- Keep components small and focused

### State Management

- Local state with useState for component-specific state
- Custom hooks for shared logic
- WebSocket client for real-time data

### Error Handling

- Error boundaries for React errors
- Try-catch blocks for async operations
- User-friendly error messages
- Retry logic for failed API calls

## Troubleshooting

### Backend Connection Issues

If you see "Failed to load chart data" errors:

1. Ensure backend is running on http://localhost:8000
2. Check CORS configuration in backend
3. Verify API endpoints are accessible

### WebSocket Connection Issues

If real-time updates aren't working:

1. Check WebSocket URL in `websocket.ts`
2. Verify backend WebSocket server is running
3. Check browser console for connection errors

### Build Issues

If build fails:

1. Delete `node_modules` and `package-lock.json`
2. Run `npm install`
3. Clear Vite cache: `rm -rf node_modules/.vite`

## License

Private - For internal use only
