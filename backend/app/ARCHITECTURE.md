# Backend Architecture Documentation

## Overview

The Trading Application backend is built with FastAPI and follows a clean, modular architecture with clear separation of concerns.

## Architecture Patterns

### Layered Architecture

```
┌─────────────────────────────────────┐
│         API Endpoints               │  ← HTTP/WebSocket interfaces
├─────────────────────────────────────┤
│      Business Logic Layer           │  ← Services and strategies
├─────────────────────────────────────┤
│       Data Access Layer             │  ← Models and repositories
├─────────────────────────────────────┤
│         Database                    │  ← PostgreSQL
└─────────────────────────────────────┘
```

### Dependency Injection

FastAPI's dependency injection system is used for:
- Database sessions (`get_db()`)
- Authentication (future)
- Configuration access

### Repository Pattern (Future)

Will be implemented in Phase 2 for data access abstraction.

## Directory Structure

### `/app/core/` - Core Infrastructure

**Purpose:** Shared utilities, configuration, and cross-cutting concerns

- `config.py` - Pydantic Settings for environment-based configuration
  - Loads `.env` variables
  - Validates required API keys
  - Provides environment detection (dev/prod)

- `logging.py` - Centralized logging setup
  - JSON formatted file logs with rotation
  - Console output for development
  - Request/response timing middleware

### `/app/models/` - Database Models

**Purpose:** SQLAlchemy ORM models representing the database schema

All models inherit from `BaseModel` which provides:
- `id` (primary key)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Models:**

1. **Strategy** - Trading strategy configuration
   - Name, description, parameters (JSONB)
   - Active/inactive status
   - One-to-many: trades, signals, events

2. **Stock** - Stock/symbol master data
   - Symbol (unique), name, exchange
   - One-to-many: trades, signals, stock_data, indicators

3. **Trade** - Complete trade lifecycle
   - Entry/exit prices and times
   - P&L calculations
   - Risk management (stop-loss, take-profit)
   - Market context (JSONB for indicator snapshots)
   - Many-to-one: strategy, stock

4. **Signal** - Generated trade signals
   - Signal type (BUY/SELL/HOLD)
   - Execution status
   - Reasons and indicator values (JSONB)
   - Many-to-one: strategy, stock

5. **Order** - Order management
   - Order type, side, quantity
   - Limit/stop prices
   - Broker order ID for tracking
   - Many-to-one: trade, stock

6. **StockData** - OHLCV time-series
   - Open, high, low, close, volume
   - Timestamp for each bar
   - Many-to-one: stock

7. **Indicator** - Calculated technical indicators
   - Indicator name (MACD, RSI, etc.)
   - Value and timestamp
   - Additional metadata (JSONB)
   - Many-to-one: stock

8. **StrategyEvent** - Event logging
   - Event type, severity, message
   - Metadata (JSONB)
   - Many-to-one: strategy

### `/app/api/` - API Layer

**Purpose:** HTTP endpoints and WebSocket connections

- `endpoints/` - Route handlers organized by domain
- `deps.py` - Shared dependencies (DB session, auth)

### `/app/db/` - Database Layer

**Purpose:** Database connection and session management

- `base.py` - Imports all models for Alembic autogenerate
- `session.py` - SQLAlchemy engine and session factory

### `/alembic/` - Database Migrations

**Purpose:** Version-controlled schema changes

- `versions/` - Migration scripts
- `env.py` - Migration environment (configured to use app models)

### `/tests/` - Unit Tests

**Purpose:** Test coverage for core functionality

- `conftest.py` - Shared fixtures (test DB, client)
- `test_models.py` - Model CRUD and relationships
- `test_config.py` - Configuration validation
- `test_health.py` - API endpoint tests

## Database Schema Details

### Relationships

```
Strategy (1) ──────── (many) Trade
   │                       │
   │                       └─── (many-to-1) Stock
   │
   ├─── (many) Signal ────── (many-to-1) Stock
   │
   └─── (many) StrategyEvent

Stock (1) ────── (many) StockData
  │
  └──────────── (many) Indicator

Trade (1) ────── (many) Order
```

### Indexing Strategy

**Performance Indexes:**
- All foreign keys indexed
- Timestamp fields indexed for time-range queries
- Unique constraints on business keys (strategy.name, stock.symbol)

**Query Patterns:**
- Find trades by strategy: `trades.strategy_id`
- Time-range queries: `trades.entry_time`, `trades.exit_time`
- Signal lookup: `trade_signals.signal_time`, `trade_signals.stock_id`

## Configuration Management

### Environment-Based Configuration

The application uses Pydantic Settings for type-safe configuration:

```python
from app.core.config import settings

# Access configuration
database_url = settings.DATABASE_URL
api_key = settings.TWELVE_DATA_API_KEY

# Environment checks
if settings.is_development:
    # Development-only code
```

### Validation

Configuration validation is performed on startup:
- Required API keys checked
- Database URL format validated
- CORS origins parsed correctly

## Logging

### Log Levels

- **DEBUG:** Development only, verbose output
- **INFO:** Production default, key events
- **WARNING:** Potential issues
- **ERROR:** Errors that need attention
- **CRITICAL:** System failures

### Log Files

- Location: `backend/logs/trading_app.log`
- Format: JSON for structured parsing
- Rotation: Daily, keeps 30 days
- Fields: timestamp, level, message, context

### Request Logging

All HTTP requests automatically logged with:
- Method, path, client IP
- Status code, process time
- Custom header: `X-Process-Time`

## Testing Strategy

### Test Database

- In-memory SQLite for fast, isolated tests
- Fresh database for each test function
- Fixtures for common test data

### Coverage Target

- Minimum: 70%
- Current: 87%
- Focus on business logic and models

### Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_models.py -v

# Run only unit tests
pytest -m unit
```

## Future Phases

### Phase 2: Market Data & Indicators
- Twelve Data API integration
- Technical indicator calculation
- Real-time data streaming

### Phase 3: Signal Generation
- MACD/RSI strategy implementation
- Backtesting framework
- Signal evaluation logic

### Phase 4: Trading Dashboard
- React frontend
- Real-time charts
- Trade monitoring

### Phase 5: Broker Integration
- Interactive Brokers connection
- Live order execution
- Position management

## Development Guidelines

### Code Style

- Black formatter (line length: 88)
- Flake8 linting
- Type hints with mypy

### Git Workflow

- Feature branches from `main`
- Conventional commits
- PR reviews required

### Database Changes

1. Modify models in `app/models/`
2. Import in `app/db/base.py`
3. Generate migration: `alembic revision --autogenerate -m "description"`
4. Review migration file
5. Apply: `alembic upgrade head`

### Adding Endpoints

1. Create endpoint file in `app/api/endpoints/`
2. Define routes with dependencies
3. Include router in `app/main.py`
4. Write tests in `tests/test_<endpoint>.py`

## Performance Considerations

- Connection pooling configured (5 connections, 10 overflow)
- Redis caching for frequently accessed data (future)
- Indexed queries for time-range operations
- JSON fields for flexible metadata without schema changes

## Security

- Environment variables for sensitive data
- CORS configured for allowed origins
- Input validation with Pydantic
- SQL injection prevention via ORM
- Secrets not committed to git

## Monitoring

- Structured JSON logs for parsing/analysis
- Health check endpoint for uptime monitoring
- Request timing in headers and logs
- Database connection health checks
