"""Test daily loss limit detector."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.risk.loss_limit_detector import LossLimitDetector
from app.database import SessionLocal
from app.models.strategy import Strategy
from app.models.stock import Stock
from app.models.trade import Trade
from datetime import datetime, timezone

def test_loss_limit():
    """Test consecutive loss tracking and auto-pause."""

    db = SessionLocal()
    detector = LossLimitDetector(db)

    try:
        # Get or create test strategy
        strategy = db.query(Strategy).filter(Strategy.name == "Test Strategy").first()
        if not strategy:
            strategy = Strategy(
                name="Test Strategy",
                description="Test strategy for loss limit",
                parameters={"stop_loss_pct": 0.05, "take_profit_pct": 0.10},
                status="active",
                consecutive_losses_today=0
            )
            db.add(strategy)
            db.commit()
            db.refresh(strategy)
        else:
            # Reset strategy state
            strategy.status = "active"
            strategy.consecutive_losses_today = 0
            db.commit()

        # Get test stock
        stock = db.query(Stock).filter(Stock.symbol == "AAPL").first()
        if not stock:
            print("ERROR: AAPL not in database. Please add it first.")
            return

        print("\n" + "="*60)
        print("DAILY LOSS LIMIT TEST")
        print("="*60)

        # Simulate 3 consecutive losing trades
        print("\nSimulating 3 consecutive losing trades...\n")

        for i in range(1, 4):
            # Create a losing trade
            trade = Trade(
                strategy_id=strategy.id,
                stock_id=stock.id,
                entry_time=datetime.now(timezone.utc),
                entry_price=100.0,
                quantity=10,
                exit_time=datetime.now(timezone.utc),
                exit_price=95.0,
                profit_loss=-50.0,  # Loss of $50
                trade_type="LONG",
                status="CLOSED"
            )
            db.add(trade)
            db.commit()
            db.refresh(trade)

            print(f"Loss #{i}:")
            print(f"  Trade ID: {trade.id}")
            print(f"  P&L: ${trade.profit_loss:.2f}")

            # Track the outcome
            detector.track_trade_outcome(trade.id)

            # Get strategy status
            status = detector.get_strategy_status(strategy.id)
            print(f"  Consecutive Losses: {status['consecutive_losses_today']}/{status['loss_limit']}")
            print(f"  Strategy Status: {status['status']}")
            print(f"  Is Paused: {status['is_paused']}")

            if status['is_paused']:
                print(f"  ⚠️  STRATEGY AUTO-PAUSED ON LOSS #{i}")

            print()

        # Verify final state
        db.refresh(strategy)

        print("="*60)
        print("VERIFICATION:")
        print("="*60)
        print(f"✓ Consecutive Losses: {strategy.consecutive_losses_today}")
        print(f"✓ Strategy Status: {strategy.status}")
        print(f"✓ Expected: Status should be 'paused' after 3 losses")
        print(f"✓ Actual: {'PASS ✅' if strategy.status == 'paused' else 'FAIL ❌'}")

        # Test win resetting counter
        print("\n" + "="*60)
        print("Testing Win Reset...")
        print("="*60)

        # Reset strategy to active
        strategy.status = "active"
        strategy.consecutive_losses_today = 2  # Simulate 2 losses
        db.commit()

        print(f"Starting state: {strategy.consecutive_losses_today} consecutive losses")

        # Create a winning trade
        win_trade = Trade(
            strategy_id=strategy.id,
            stock_id=stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=10,
            exit_time=datetime.now(timezone.utc),
            exit_price=105.0,
            profit_loss=50.0,  # Win of $50
            trade_type="LONG",
            status="CLOSED"
        )
        db.add(win_trade)
        db.commit()
        db.refresh(win_trade)

        print(f"\nWin Trade:")
        print(f"  Trade ID: {win_trade.id}")
        print(f"  P&L: ${win_trade.profit_loss:.2f}")

        detector.track_trade_outcome(win_trade.id)

        db.refresh(strategy)
        print(f"\nAfter win: {strategy.consecutive_losses_today} consecutive losses")
        print(f"✓ Expected: Counter should be reset to 0")
        print(f"✓ Actual: {'PASS ✅' if strategy.consecutive_losses_today == 0 else 'FAIL ❌'}")

        print("\n" + "="*60)
        print("✓ Loss limit test complete!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_loss_limit()
