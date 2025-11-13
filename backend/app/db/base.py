"""Import all models here for Alembic to detect them."""
from sqlalchemy.ext.declarative import declarative_base

# Create base class for models
Base = declarative_base()

# Import all models here so Alembic can detect them
# These will be uncommented once models are created
# from app.models.strategy import Strategy
# from app.models.stock import Stock
# from app.models.trade import Trade
# from app.models.signal import Signal
# from app.models.order import Order
# from app.models.stock_data import StockData
# from app.models.indicator import Indicator
# from app.models.strategy_event import StrategyEvent
