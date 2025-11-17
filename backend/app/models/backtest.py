"""Backtest models for storing backtesting results."""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, JSON, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class BacktestRun(BaseModel):
    """Backtest run results model."""

    __tablename__ = "backtest_runs"

    # Foreign keys
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)

    # Backtest parameters
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Numeric(15, 2), nullable=False, default=100000.00)
    slippage_pct = Column(Numeric(5, 4), nullable=False, default=0.001)  # 0.1%
    commission_per_trade = Column(Numeric(10, 2), nullable=False, default=1.00)
    strategy_parameters = Column(JSON, nullable=False)  # Strategy params at time of backtest

    # Results summary
    final_equity = Column(Numeric(15, 2), nullable=False)
    total_return_pct = Column(Numeric(10, 4), nullable=False)
    annualized_return_pct = Column(Numeric(10, 4), nullable=True)
    sharpe_ratio = Column(Numeric(10, 4), nullable=True)
    max_drawdown_pct = Column(Numeric(10, 4), nullable=True)
    win_rate_pct = Column(Numeric(10, 4), nullable=True)
    profit_factor = Column(Numeric(10, 4), nullable=True)

    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    avg_win = Column(Numeric(15, 2), nullable=True)
    avg_loss = Column(Numeric(15, 2), nullable=True)
    largest_win = Column(Numeric(15, 2), nullable=True)
    largest_loss = Column(Numeric(15, 2), nullable=True)

    # Execution metadata
    execution_time_seconds = Column(Numeric(10, 2), nullable=True)
    bars_processed = Column(Integer, nullable=True)

    # Relationships
    strategy = relationship("Strategy", backref="backtest_runs")
    stock = relationship("Stock", backref="backtest_runs")

    # Unique constraint: one backtest per combination (excluding JSON parameters)
    # Note: Multiple backtests with different parameters are allowed for same stock/dates
    __table_args__ = (
        UniqueConstraint(
            'strategy_id',
            'stock_id',
            'start_date',
            'end_date',
            name='uq_backtest_run'
        ),
    )

    def __repr__(self):
        return (
            f"<BacktestRun(id={self.id}, stock_id={self.stock_id}, "
            f"return={self.total_return_pct}%, sharpe={self.sharpe_ratio})>"
        )


class BacktestTrade(BaseModel):
    """Individual trade from a backtest."""

    __tablename__ = "backtest_trades"

    # Foreign key
    backtest_run_id = Column(Integer, ForeignKey("backtest_runs.id"), nullable=False, index=True)

    # Trade details
    trade_number = Column(Integer, nullable=False)  # Sequential trade number in backtest
    entry_date = Column(Date, nullable=False)
    entry_price = Column(Numeric(10, 2), nullable=False)
    entry_signal = Column(String(20), nullable=False)  # BUY signal type

    exit_date = Column(Date, nullable=True)
    exit_price = Column(Numeric(10, 2), nullable=True)
    exit_signal = Column(String(20), nullable=True)  # SELL, STOP_LOSS, TAKE_PROFIT

    # Position details
    shares = Column(Integer, nullable=False)
    position_value = Column(Numeric(15, 2), nullable=False)

    # P&L
    gross_pnl = Column(Numeric(15, 2), nullable=True)
    commission_paid = Column(Numeric(10, 2), nullable=False)
    slippage_cost = Column(Numeric(10, 2), nullable=False)
    net_pnl = Column(Numeric(15, 2), nullable=True)
    return_pct = Column(Numeric(10, 4), nullable=True)

    # Trade metadata
    holding_period_days = Column(Integer, nullable=True)
    is_winner = Column(Boolean, nullable=True)

    # Signal context (snapshot at entry)
    entry_indicators = Column(JSON, nullable=True)
    entry_market_context = Column(JSON, nullable=True)

    # Relationship
    backtest_run = relationship("BacktestRun", backref="trades")

    def __repr__(self):
        return (
            f"<BacktestTrade(id={self.id}, entry={self.entry_date}, "
            f"exit={self.exit_date}, pnl={self.net_pnl})>"
        )


class BacktestEquityCurve(BaseModel):
    """Daily equity curve snapshot during backtest."""

    __tablename__ = "backtest_equity_curve"

    # Foreign key
    backtest_run_id = Column(Integer, ForeignKey("backtest_runs.id"), nullable=False, index=True)

    # Date and equity
    date = Column(Date, nullable=False, index=True)
    equity = Column(Numeric(15, 2), nullable=False)
    cash = Column(Numeric(15, 2), nullable=False)
    position_value = Column(Numeric(15, 2), nullable=False, default=0.00)

    # Daily metrics
    daily_return_pct = Column(Numeric(10, 4), nullable=True)
    drawdown_pct = Column(Numeric(10, 4), nullable=True)  # Current drawdown from peak

    # Relationship
    backtest_run = relationship("BacktestRun", backref="equity_curve")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint(
            'backtest_run_id',
            'date',
            name='uq_backtest_equity_date'
        ),
    )

    def __repr__(self):
        return f"<BacktestEquityCurve(id={self.id}, date={self.date}, equity={self.equity})>"
