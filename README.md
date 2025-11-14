# Trading Application - MACD/RSI Strategy

An algorithmic trading application implementing a MACD/RSI crossover strategy with Interactive Brokers integration.

## MVP Goals

- Automated trading based on MACD and RSI technical indicators
- Real-time market data integration via Twelve Data API
- Trade execution through Interactive Brokers
- Comprehensive trade logging and performance tracking
- Risk management with stop-loss and take-profit orders
- Web dashboard for monitoring and control

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.9+)
- **Database:** PostgreSQL 16
- **Cache:** Redis 7
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Testing:** pytest with 87% coverage
- **Technical Analysis:** ta library
- **Broker Integration:** ib_insync

### Frontend (Coming in Phase 2)
- React with TypeScript
- Real-time updates via WebSocket
- Chart visualization

### Infrastructure
- Docker Compose for services
- Structured JSON logging
- Configuration management with Pydantic

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── core/
│   │   ├── config.py        # Settings and configuration
│   │   └── logging.py       # Logging setup
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── strategy.py      # Trading strategies
│   │   ├── stock.py         # Stock/symbol data
│   │   ├── trade.py         # Trade execution records
│   │   ├── signal.py        # Trade signals
│   │   ├── order.py         # Order management
│   │   ├── stock_data.py    # OHLCV time-series
│   │   ├── indicator.py     # Technical indicators
│   │   └── strategy_event.py # Event logging
│   ├── api/
│   │   ├── endpoints/       # API route handlers
│   │   └── deps.py          # Shared dependencies
│   └── db/
│       ├── base.py          # Base model imports
│       └── session.py       # Database session
├── alembic/                 # Database migrations
├── tests/                   # Unit tests
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
└── pytest.ini              # Test configuration

frontend/                    # React application (Phase 2)
```

## Quick Start

### Prerequisites

- Python 3.9+
- Docker Desktop
- PostgreSQL client (optional, for manual DB access)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Trading
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Start Docker services:**
   ```bash
   docker compose up -d
   ```

4. **Set up Python environment:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

7. **Access the application:**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Running Tests

```bash
cd backend
source venv/bin/activate
pytest -v --cov=app
```

## Environment Variables

All environment variables should be defined in the `.env` file. See `.env.example` for the template.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `TWELVE_DATA_API_KEY` | Market data API key | Get from https://twelvedata.com |

### Optional Variables (Phase 5)

| Variable | Description | Default |
|----------|-------------|---------|
| `IBKR_USERNAME` | Interactive Brokers username | - |
| `IBKR_PASSWORD` | Interactive Brokers password | - |
| `IBKR_TRADING_MODE` | Trading mode (paper/live) | `paper` |
| `IBKR_PORT` | TWS/Gateway port | `7497` |

### Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment mode | `development` |
| `DEBUG` | Debug mode | `True` |
| `LOG_LEVEL` | Logging level | `DEBUG` |
| `SECRET_KEY` | JWT secret key | Change in production |

## API Credentials Setup

### Twelve Data API (Required)

1. Sign up at https://twelvedata.com
2. Choose the free tier (800 API calls/day)
3. Generate an API key from your dashboard
4. Add to `.env`: `TWELVE_DATA_API_KEY=your_key_here`

### Interactive Brokers (Phase 5)

IBKR integration will be implemented in Phase 5. For now:
- Credentials are optional
- Trading mode defaults to `paper` for safety
- TWS/Gateway port defaults to `7497` (paper trading port)

Documentation for IBKR setup will be added in Phase 5 when implementing broker integration.

## Database Schema

The application uses 8 core tables:

- `strategies` - Trading strategy configurations
- `stocks` - Stock/symbol master data
- `trades` - Trade execution records with P&L
- `trade_signals` - Generated buy/sell signals
- `orders` - Order management and execution
- `stock_data` - OHLCV price time-series
- `indicators` - Calculated technical indicators
- `strategy_events` - Strategy execution logs

See `backend/app/ARCHITECTURE.md` for detailed schema documentation.

## Development

### Running the Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Accessing the Database

```bash
# Via Docker
docker exec -it trading_postgres psql -U trading_user -d trading_db

# Direct connection (if PostgreSQL client installed)
psql postgresql://trading_user:trading_password@localhost:5432/trading_db
```

## Troubleshooting

### Port Already in Use (5432)

If you get "address already in use" for port 5432:

```bash
# Check if system PostgreSQL is running
brew services list | grep postgres

# Stop system PostgreSQL
brew services stop postgresql@14

# Or find and kill the process
sudo lsof -i :5432
sudo kill -9 <PID>
```

### Docker Services Not Starting

```bash
# Check Docker Desktop is running (look for whale icon in menu bar)
docker ps

# Restart services
docker compose down
docker compose up -d

# View logs
docker compose logs postgres
docker compose logs redis
```

### Migration Errors

```bash
# Reset database (WARNING: destroys all data)
docker compose down -v
docker compose up -d
alembic upgrade head

# Check migration status
alembic current
alembic history
```

### Tests Failing

```bash
# Run tests with verbose output
pytest -vv

# Run specific test file
pytest tests/test_models.py -v

# Run with coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Import Errors

Make sure you're in the backend directory and virtual environment is activated:

```bash
cd backend
source venv/bin/activate
python -c "from app.core.config import settings; print('OK')"
```

## Phase 1 Status

**Completed:**
- ✅ Project structure and development environment
- ✅ Docker services (PostgreSQL, Redis)
- ✅ Database schema and migrations
- ✅ FastAPI application with WebSocket support
- ✅ All 8 core database models
- ✅ Configuration management with validation
- ✅ Comprehensive logging infrastructure
- ✅ Unit tests with 87% coverage

**Next Phase:**
- Phase 2: Market data fetching and technical indicators
- Phase 3: Signal generation and strategy logic
- Phase 4: Trading dashboard UI
- Phase 5: Broker integration and live trading

## License

Proprietary - All Rights Reserved

## Support

For issues or questions, please contact the development team.
