"""Test position sizing calculator."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.trading.ibkr_client import IBKRClient
from app.services.risk.position_sizer import PositionSizer
from app.core.config import settings

def test_position_sizing():
    """Test position size calculations with 2% risk rule."""

    # Connect to IBKR
    client = IBKRClient(
        host=settings.IBKR_HOST,
        port=settings.IBKR_PORT,
        client_id=settings.IBKR_CLIENT_ID
    )
    client.connect()

    try:
        sizer = PositionSizer(client)

        print("\n" + "="*60)
        print("POSITION SIZING TEST")
        print("="*60)

        # Get actual portfolio value
        portfolio_value = sizer.get_portfolio_value()
        print(f"\nActual Portfolio Value: ${portfolio_value:,.2f}")

        # Test 1: Standard calculation
        print("\n[TEST 1] Standard 2% Risk Calculation:")
        print(f"  Portfolio: $10,000 (example)")
        print(f"  Entry: $100")
        print(f"  Stop: $95 (5% risk per share)")

        result = sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=95.0,
            portfolio_value=10000.0
        )

        print(f"\n  Results:")
        print(f"    Quantity: {result['quantity']} shares")
        print(f"    Position Value: ${result['position_value']:,.2f}")
        print(f"    Risk Amount: ${result['risk_amount']:,.2f}")
        print(f"    Risk %: {result['risk_percent']:.2f}%")
        print(f"    Position %: {result['position_percent']:.2f}%")

        # Expected: 40 shares
        expected_shares = 40
        print(f"\n  Expected: {expected_shares} shares")
        print(f"  Actual: {result['quantity']} shares")
        print(f"  Result: {'✅ PASS' if result['quantity'] == expected_shares else '❌ FAIL'}")

        # Test 2: Position cap (20%)
        print("\n[TEST 2] Position Size Cap (20% limit):")
        print(f"  Portfolio: $10,000")
        print(f"  Entry: $100")
        print(f"  Stop: $99 (only 1% risk per share)")

        result2 = sizer.calculate_position_size(
            entry_price=100.0,
            stop_loss=99.0,
            portfolio_value=10000.0
        )

        print(f"\n  Results:")
        print(f"    Quantity: {result2['quantity']} shares")
        print(f"    Position Value: ${result2['position_value']:,.2f}")
        print(f"    Position %: {result2['position_percent']:.2f}%")
        print(f"    Capped: {result2['capped']}")

        # Should be capped at 20 shares (20% of $10k = $2k / $100)
        print(f"\n  Max Position: 20% = $2,000 = 20 shares")
        print(f"  Result: {'✅ PASS' if result2['position_percent'] <= 20 else '❌ FAIL'}")

        # Test 3: Real portfolio calculation
        print("\n[TEST 3] Real Portfolio Calculation:")
        print(f"  Portfolio: ${portfolio_value:,.2f} (actual)")
        print(f"  Entry: $150")
        print(f"  Stop: $145 (3.33% risk per share)")

        result3 = sizer.calculate_position_size(
            entry_price=150.0,
            stop_loss=145.0
        )

        print(f"\n  Results:")
        print(f"    Quantity: {result3['quantity']} shares")
        print(f"    Position Value: ${result3['position_value']:,.2f}")
        print(f"    Risk Amount: ${result3['risk_amount']:,.2f}")
        print(f"    Risk %: {result3['risk_percent']:.2f}%")
        print(f"    Position %: {result3['position_percent']:.2f}%")

        # Validate position
        is_valid, error = sizer.validate_position(result3)
        print(f"\n  Validation: {'✅ PASS' if is_valid else f'❌ FAIL - {error}'}")

        print("\n" + "="*60)
        print("✓ Position sizing tests complete!")
        print("="*60)

    finally:
        client.disconnect()

if __name__ == "__main__":
    test_position_sizing()
