"""Tests for database models."""
import pytest
from datetime import datetime
from app.models.strategy import Strategy
from app.models.stock import Stock
from app.models.trade import Trade


@pytest.mark.unit
def test_create_strategy(db_session, sample_strategy_data):
    """Test creating a strategy."""
    strategy = Strategy(**sample_strategy_data)
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)

    assert strategy.id is not None
    assert strategy.name == sample_strategy_data["name"]
    assert strategy.active is True
    assert strategy.parameters == sample_strategy_data["parameters"]
    assert strategy.created_at is not None
    assert strategy.updated_at is not None


@pytest.mark.unit
def test_create_stock(db_session, sample_stock_data):
    """Test creating a stock."""
    stock = Stock(**sample_stock_data)
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)

    assert stock.id is not None
    assert stock.symbol == sample_stock_data["symbol"]
    assert stock.name == sample_stock_data["name"]
    assert stock.exchange == sample_stock_data["exchange"]


@pytest.mark.unit
def test_strategy_stock_relationship(db_session, sample_strategy_data, sample_stock_data):
    """Test relationships between models."""
    # Create strategy and stock
    strategy = Strategy(**sample_strategy_data)
    stock = Stock(**sample_stock_data)

    db_session.add(strategy)
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(strategy)
    db_session.refresh(stock)

    # Create trade linking them
    trade = Trade(
        strategy_id=strategy.id,
        stock_id=stock.id,
        entry_time=datetime(2025, 1, 1, 10, 0, 0),
        entry_price=150.00,
        quantity=10,
        trade_type="LONG",
        status="OPEN"
    )

    db_session.add(trade)
    db_session.commit()
    db_session.refresh(trade)

    assert trade.id is not None
    assert trade.strategy.name == sample_strategy_data["name"]
    assert trade.stock.symbol == sample_stock_data["symbol"]


@pytest.mark.unit
def test_strategy_unique_name_constraint(db_session, sample_strategy_data):
    """Test that strategy names must be unique."""
    strategy1 = Strategy(**sample_strategy_data)
    db_session.add(strategy1)
    db_session.commit()

    # Try to create another strategy with the same name
    strategy2 = Strategy(**sample_strategy_data)
    db_session.add(strategy2)

    with pytest.raises(Exception):  # SQLAlchemy IntegrityError
        db_session.commit()
