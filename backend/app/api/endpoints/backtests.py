"""Backtest API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import date as date_type

from app.api.deps import get_db
from app.schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    BacktestMetrics,
    BacktestListResponse,
    BacktestListItem,
    BacktestTradesResponse,
    BacktestTradeSchema,
    BacktestEquityCurveResponse,
    EquityCurvePoint
)
from app.services.backtesting.backtest_engine import BacktestEngine
from app.models.backtest import BacktestRun, BacktestTrade, BacktestEquityCurve
from app.core.logging import get_logger

logger = get_logger("backtests_api")

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("/", response_model=BacktestResponse, status_code=201)
async def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db)
):
    """
    Run a new backtest.

    This executes a strategy backtest on historical data and stores the results.

    Args:
        request: Backtest parameters
        db: Database session

    Returns:
        Backtest results with performance metrics

    Example:
    ```json
    {
        "strategy_id": 1,
        "symbol": "AAPL",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "initial_capital": 100000.0
    }
    ```
    """
    logger.info(f"Backtest request: {request.symbol} ({request.start_date} to {request.end_date})")

    try:
        engine = BacktestEngine(db)

        # Parse dates
        start_date = date_type.fromisoformat(request.start_date)
        end_date = date_type.fromisoformat(request.end_date)

        # Run backtest
        results = engine.run_backtest(
            strategy_id=request.strategy_id,
            symbol=request.symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=request.initial_capital,
            slippage_pct=request.slippage_pct,
            commission_per_trade=request.commission_per_trade
        )

        # Build response
        metrics = BacktestMetrics(
            total_return_pct=results['total_return_pct'],
            annualized_return_pct=results.get('annualized_return_pct'),
            sharpe_ratio=results.get('sharpe_ratio'),
            max_drawdown_pct=results.get('max_drawdown_pct'),
            win_rate_pct=results.get('win_rate_pct'),
            profit_factor=results.get('profit_factor'),
            total_trades=results['total_trades'],
            winning_trades=results['winning_trades'],
            losing_trades=results['losing_trades'],
            avg_win=results.get('avg_win'),
            avg_loss=results.get('avg_loss'),
            largest_win=results.get('largest_win'),
            largest_loss=results.get('largest_loss')
        )

        response = BacktestResponse(
            backtest_id=results['backtest_id'],
            symbol=results['symbol'],
            strategy_name="Strategy",  # Will get from DB
            start_date=results['start_date'],
            end_date=results['end_date'],
            initial_capital=results['initial_capital'],
            final_equity=results['final_equity'],
            metrics=metrics,
            execution_time_seconds=results.get('execution_time_seconds'),
            bars_processed=results['bars_processed'],
            status="ok"
        )

        logger.info(f"Backtest {results['backtest_id']} completed: return={results['total_return_pct']:.2f}%")

        return response

    except ValueError as e:
        logger.error(f"Invalid backtest request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Backtest execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.get("/", response_model=BacktestListResponse)
async def list_backtests(
    strategy_id: Optional[int] = None,
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all backtests with optional filters."""
    logger.info("List backtests request")

    try:
        query = db.query(BacktestRun)

        if strategy_id:
            query = query.filter(BacktestRun.strategy_id == strategy_id)

        if symbol:
            query = query.join(BacktestRun.stock).filter(Stock.symbol == symbol.upper())

        backtests = query.order_by(BacktestRun.created_at.desc()).limit(50).all()

        items = [
            BacktestListItem(
                backtest_id=b.id,
                symbol=b.stock.symbol,
                strategy_name=b.strategy.name,
                start_date=b.start_date,
                end_date=b.end_date,
                total_return_pct=float(b.total_return_pct),
                sharpe_ratio=float(b.sharpe_ratio) if b.sharpe_ratio else None,
                max_drawdown_pct=float(b.max_drawdown_pct) if b.max_drawdown_pct else None,
                total_trades=b.total_trades,
                created_at=b.created_at.isoformat()
            )
            for b in backtests
        ]

        return BacktestListResponse(
            backtests=items,
            total=len(items),
            status="ok"
        )

    except Exception as e:
        logger.error(f"Error listing backtests: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest(
    backtest_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed backtest results."""
    logger.info(f"Get backtest: {backtest_id}")

    try:
        engine = BacktestEngine(db)
        results = engine.get_backtest_results(backtest_id)

        backtest = db.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()

        metrics = BacktestMetrics(
            total_return_pct=float(backtest.total_return_pct),
            annualized_return_pct=float(backtest.annualized_return_pct) if backtest.annualized_return_pct else None,
            sharpe_ratio=float(backtest.sharpe_ratio) if backtest.sharpe_ratio else None,
            max_drawdown_pct=float(backtest.max_drawdown_pct) if backtest.max_drawdown_pct else None,
            win_rate_pct=float(backtest.win_rate_pct) if backtest.win_rate_pct else None,
            profit_factor=float(backtest.profit_factor) if backtest.profit_factor else None,
            total_trades=backtest.total_trades,
            winning_trades=backtest.winning_trades,
            losing_trades=backtest.losing_trades,
            avg_win=float(backtest.avg_win) if backtest.avg_win else None,
            avg_loss=float(backtest.avg_loss) if backtest.avg_loss else None,
            largest_win=float(backtest.largest_win) if backtest.largest_win else None,
            largest_loss=float(backtest.largest_loss) if backtest.largest_loss else None
        )

        return BacktestResponse(
            backtest_id=backtest.id,
            symbol=backtest.stock.symbol,
            strategy_name=backtest.strategy.name,
            start_date=backtest.start_date,
            end_date=backtest.end_date,
            initial_capital=float(backtest.initial_capital),
            final_equity=float(backtest.final_equity),
            metrics=metrics,
            execution_time_seconds=float(backtest.execution_time_seconds) if backtest.execution_time_seconds else None,
            bars_processed=backtest.bars_processed,
            status="ok"
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(f"Error getting backtest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}/trades", response_model=BacktestTradesResponse)
async def get_backtest_trades(
    backtest_id: int,
    db: Session = Depends(get_db)
):
    """Get all trades from a backtest."""
    logger.info(f"Get backtest trades: {backtest_id}")

    try:
        backtest = db.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()

        if not backtest:
            raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")

        trades = db.query(BacktestTrade).filter(
            BacktestTrade.backtest_run_id == backtest_id
        ).order_by(BacktestTrade.trade_number).all()

        trade_schemas = [
            BacktestTradeSchema(
                trade_number=t.trade_number,
                entry_date=t.entry_date,
                entry_price=float(t.entry_price),
                exit_date=t.exit_date,
                exit_price=float(t.exit_price) if t.exit_price else None,
                shares=t.shares,
                entry_signal=t.entry_signal,
                exit_signal=t.exit_signal,
                gross_pnl=float(t.gross_pnl) if t.gross_pnl else None,
                net_pnl=float(t.net_pnl) if t.net_pnl else None,
                return_pct=float(t.return_pct) if t.return_pct else None,
                holding_period_days=t.holding_period_days,
                is_winner=t.is_winner
            )
            for t in trades
        ]

        return BacktestTradesResponse(
            backtest_id=backtest_id,
            symbol=backtest.stock.symbol,
            trades=trade_schemas,
            total_trades=len(trade_schemas),
            status="ok"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting trades: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{backtest_id}/equity-curve", response_model=BacktestEquityCurveResponse)
async def get_equity_curve(
    backtest_id: int,
    db: Session = Depends(get_db)
):
    """Get equity curve data for charting."""
    logger.info(f"Get equity curve: {backtest_id}")

    try:
        backtest = db.query(BacktestRun).filter(BacktestRun.id == backtest_id).first()

        if not backtest:
            raise HTTPException(status_code=404, detail=f"Backtest {backtest_id} not found")

        equity_points = db.query(BacktestEquityCurve).filter(
            BacktestEquityCurve.backtest_run_id == backtest_id
        ).order_by(BacktestEquityCurve.date).all()

        curve_data = [
            EquityCurvePoint(
                date=p.date,
                equity=float(p.equity),
                cash=float(p.cash),
                position_value=float(p.position_value)
            )
            for p in equity_points
        ]

        return BacktestEquityCurveResponse(
            backtest_id=backtest_id,
            symbol=backtest.stock.symbol,
            equity_curve=curve_data,
            total_points=len(curve_data),
            status="ok"
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error getting equity curve: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


from app.models.stock import Stock
from typing import Optional
