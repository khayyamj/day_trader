"""Test risk manager validation rules."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.trading.ibkr_client import IBKRClient
from app.services.risk.position_sizer import PositionSizer
from app.services.risk.risk_manager import RiskManager
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.stock import Stock
from app.models.strategy import Strategy
from app.models.trade import Trade
from datetime import datetime, timezone

def test_risk_validations():
    """Test all risk validation rules."""

    # Setup
    client = IBKRClient(
        host=settings.IBKR_HOST,
        port=settings.IBKR_PORT,
        client_id=settings.IBKR_CLIENT_ID
    )
    client.connect()

    db = SessionLocal()
    position_sizer = PositionSizer(client)
    risk_manager = RiskManager(client, position_sizer, db)

    try:
        # Get or create test strategy
        strategy = db.query(Strategy).filter(Strategy.name == "Test Strategy").first()
        if not strategy:
            strategy = Strategy(
                name="Test Strategy",
                description="Test strategy for validation",
                parameters={"stop_loss_pct": 0.05, "take_profit_pct": 0.10}
            )
            db.add(strategy)
            db.commit()
            db.refresh(strategy)

        # Get AAPL stock
        stock = db.query(Stock).filter(Stock.symbol == "AAPL").first()
        if not stock:
            print("ERROR: AAPL not in database. Please add it first.")
            return

        print("\n" + "="*60)
        print("RISK MANAGER VALIDATION TESTS")
        print("="*60)

        # Test 1: Duplicate Position Check
        print("\n1. Testing Duplicate Position Check...")

        # Create a fake open position
        existing_trade = Trade(
            strategy_id=strategy.id,
            stock_id=stock.id,
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=10,
            trade_type="LONG",
            status="OPEN"
        )
        db.add(existing_trade)
        db.commit()

        result = risk_manager.check_duplicate_position(strategy.id, "AAPL")
        print(f"   Result: {'❌ REJECTED' if not result.is_valid else '✅ PASSED'}")
        if not result.is_valid:
            print(f"   Reason: {result.reason}")
        print(f"   Expected: Should be REJECTED (duplicate position)")

        # Clean up
        db.delete(existing_trade)
        db.commit()

        # Test 2: No Duplicate (should pass)
        print("\n2. Testing No Duplicate (New Position)...")
        result = risk_manager.check_duplicate_position(strategy.id, "MSFT")
        print(f"   Result: {'✅ PASSED' if result.is_valid else '❌ REJECTED'}")
        print(f"   Expected: Should PASS (no existing position)")

        # Test 3: Capital Check
        print("\n3. Testing Capital Sufficiency...")
        portfolio_value = position_sizer.get_portfolio_value()
        excessive_position = portfolio_value * 2  # Try to buy 2x portfolio value

        result = risk_manager.check_sufficient_capital(excessive_position)
        print(f"   Portfolio: ${portfolio_value:,.2f}")
        print(f"   Trying to buy: ${excessive_position:,.2f}")
        print(f"   Result: {'❌ REJECTED' if not result.is_valid else '✅ PASSED'}")
        if not result.is_valid:
            print(f"   Reason: {result.reason}")
        print(f"   Expected: Should be REJECTED (insufficient capital)")

        # Test 4: Position Size Limit (20%)
        print("\n4. Testing Position Size Limit (20% cap)...")
        excessive_position_pct = portfolio_value * 0.25  # Try 25%

        result = risk_manager.check_position_size_limit(excessive_position_pct)
        print(f"   Portfolio: ${portfolio_value:,.2f}")
        print(f"   Position: ${excessive_position_pct:,.2f} (25%)")
        print(f"   Result: {'❌ REJECTED' if not result.is_valid else '✅ PASSED'}")
        if not result.is_valid:
            print(f"   Reason: {result.reason}")
        print(f"   Expected: Should be REJECTED (exceeds 20% limit)")

        # Test 5: Strategy Allocation Limit (50%)
        print("\n5. Testing Strategy Allocation Limit (50% cap)...")
        excessive_strategy_allocation = portfolio_value * 0.55  # Try 55%

        result = risk_manager.check_portfolio_allocation(
            strategy.id,
            excessive_strategy_allocation
        )
        print(f"   Portfolio: ${portfolio_value:,.2f}")
        print(f"   New Position: ${excessive_strategy_allocation:,.2f} (55%)")
        print(f"   Result: {'❌ REJECTED' if not result.is_valid else '✅ PASSED'}")
        if not result.is_valid:
            print(f"   Reason: {result.reason}")
        print(f"   Expected: Should be REJECTED (exceeds 50% strategy limit)")

        # Test 6: Daily Loss Limit Check
        print("\n6. Testing Daily Loss Limit...")

        # Simulate paused strategy
        strategy.status = 'paused'
        db.commit()

        result = risk_manager.check_daily_loss_limit(strategy.id)
        print(f"   Strategy Status: {strategy.status}")
        print(f"   Result: {'❌ REJECTED' if not result.is_valid else '✅ PASSED'}")
        if not result.is_valid:
            print(f"   Reason: {result.reason}")
        print(f"   Expected: Should be REJECTED (strategy paused)")

        # Restore strategy status
        strategy.status = 'active'
        db.commit()

        print("\n" + "="*60)
        print("✓ All risk validation tests complete!")
        print("="*60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()
        client.disconnect()

if __name__ == "__main__":
    test_risk_validations()
