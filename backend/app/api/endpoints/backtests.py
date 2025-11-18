"""Backtest API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import date as date_type
from typing import Optional

from app.api.deps import get_db
from app.models.stock import Stock
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
from app.services.backtesting.job_manager import backtest_job_manager
from app.models.backtest import BacktestRun, BacktestTrade, BacktestEquityCurve
from app.core.logging import get_logger
from app.db.session import SessionLocal

logger = get_logger("backtests_api")

router = APIRouter(prefix="/backtests", tags=["backtests"])


def execute_backtest_job(job_id: str, request_dict: dict):
    """
    Background task to execute backtest.

    Args:
        job_id: Job ID for tracking
        request_dict: Backtest request parameters
    """
    db = SessionLocal()

    try:
        # Mark job as running
        backtest_job_manager.start_job(job_id)

        # Parse request
        start_date = date_type.fromisoformat(request_dict['start_date'])
        end_date = date_type.fromisoformat(request_dict['end_date'])

        # Run backtest
        engine = BacktestEngine(db)

        results = engine.run_backtest(
            strategy_id=request_dict['strategy_id'],
            symbol=request_dict['symbol'],
            start_date=start_date,
            end_date=end_date,
            initial_capital=request_dict.get('initial_capital', 100000.0),
            slippage_pct=request_dict.get('slippage_pct', 0.001),
            commission_per_trade=request_dict.get('commission_per_trade', 1.0)
        )

        # Mark job as complete
        backtest_job_manager.complete_job(job_id, results['backtest_id'])

        logger.info(f"Job {job_id} completed successfully: backtest_id={results['backtest_id']}")

    except Exception as e:
        # Mark job as failed
        error_msg = str(e)
        backtest_job_manager.fail_job(job_id, error_msg)

        logger.error(f"Job {job_id} failed: {error_msg}")

    finally:
        db.close()


@router.post("/async", status_code=202)
async def run_backtest_async(
    request: BacktestRequest,
    background_tasks: BackgroundTasks
):
    """
    Run a backtest asynchronously (non-blocking).

    This endpoint queues the backtest for background execution and returns
    immediately with a job ID. Use the job ID to check status and retrieve
    results when complete.

    Args:
        request: Backtest parameters
        background_tasks: FastAPI background tasks

    Returns:
        Job information with job_id for tracking

    Example:
    ```json
    {
        "strategy_id": 1,
        "symbol": "AAPL",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
    ```

    Response:
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "pending",
        "message": "Backtest queued for execution"
    }
    ```

    Then check status:
    ```
    GET /api/backtests/jobs/{job_id}
    ```
    """
    logger.info(f"Async backtest request: {request.symbol}")

    try:
        # Create job
        request_dict = request.model_dump()
        job_id = backtest_job_manager.create_job(request_dict)

        # Queue backtest execution
        background_tasks.add_task(execute_backtest_job, job_id, request_dict)

        logger.info(f"Backtest job {job_id} queued")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Backtest queued for execution",
            "check_status_url": f"/api/backtests/jobs/{job_id}"
        }

    except Exception as e:
        logger.error(f"Error creating backtest job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to queue backtest: {str(e)}")


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get status of an async backtest job.

    Args:
        job_id: Job ID from async backtest request

    Returns:
        Job status and progress information

    Status values:
    - pending: Job queued, not started
    - running: Job executing
    - completed: Job finished successfully
    - failed: Job failed with error
    """
    logger.info(f"Job status request: {job_id}")

    job = backtest_job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    response = job.to_dict()

    # Add result URL if completed
    if job.status.value == "completed" and job.backtest_run_id:
        response['result_url'] = f"/api/backtests/{job.backtest_run_id}"

    return response


@router.get("/jobs")
async def list_jobs(limit: int = 50):
    """
    List recent backtest jobs.

    Args:
        limit: Maximum number of jobs to return

    Returns:
        List of job statuses
    """
    logger.info("List jobs request")

    jobs = backtest_job_manager.list_jobs(limit=limit)

    return {
        "jobs": jobs,
        "total": len(jobs),
        "status": "ok"
    }


@router.post("/", response_model=BacktestResponse, status_code=201)
async def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db)
):
    """
    Run a new backtest (synchronous).

    This executes a strategy backtest on historical data and stores the results.
    The request will block until the backtest completes.

    For long-running backtests (>1 year), consider using POST /api/backtests/async instead.

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
