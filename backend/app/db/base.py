"""Import all models here for Alembic to detect them."""
from sqlalchemy.ext.declarative import declarative_base

# Create base class for models
Base = declarative_base()

# Import all models here so Alembic can detect them
from app.models.strategy import Strategy  # noqa
from app.models.stock import Stock  # noqa
from app.models.trade import Trade  # noqa
from app.models.signal import Signal  # noqa
from app.models.order import Order  # noqa
from app.models.stock_data import StockData  # noqa
from app.models.indicator import Indicator  # noqa
from app.models.strategy_event import StrategyEvent  # noqa
