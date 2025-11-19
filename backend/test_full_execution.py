"""Test full trade execution flow: signal → validation → orders → monitoring."""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.trading.ibkr_client import IBKRClient
from app.services.trading.order_service import OrderService
from app.services.trading.execution_engine import ExecutionEngine
from app.services.risk.position_sizer import PositionSizer
from app.services.risk.risk_manager import RiskManager
from app.services.strategies.base_strategy import TradingSignal, SignalType, BaseStrategy
from app.core.config import settings
from app.database import SessionLocal
from app.models.strategy import Strategy
from app.models.stock import Stock
from app.models.order import Order
from app.models.trade import Trade

class TestStrategy(BaseStrategy):
    """Simple test strategy for execution testing."""

    def __init__(self):
        super().__init__(
            name="Test Execution Strategy",
            parameters={
                'stop_loss_pct': 0.05,      # 5% stop loss
                'take_profit_pct': 0.10     # 10% take profit
            }
        )

    def generate_signal(self, df, current_position=None):
        """Not used in this test."""
        pass

    def get_parameters(self):
        return self.parameters

    def validate_parameters(self, parameters):
        return True


def test_full_execution():
    """
    Test complete execution flow:
    1. Create trading signal
    2. Validate with risk manager
    3. Calculate position size
    4. Submit market order
    5. Submit stop-loss order (broker level)
    6. Submit take-profit order (broker level)
    7. Verify all orders in IBKR TWS
    """

    # Setup
    client = IBKRClient(
        host=settings.IBKR_HOST,
        port=settings.IBKR_PORT,
        client_id=settings.IBKR_CLIENT_ID
    )
    client.connect()

    db = SessionLocal()
    order_service = OrderService(client, db)
    position_sizer = PositionSizer(client)
    risk_manager = RiskManager(client, position_sizer, db)
    execution_engine = ExecutionEngine(
        client,
        order_service,
        position_sizer,
        risk_manager,
        db
    )

    try:
        print("\n" + "="*80)
        print("FULL TRADE EXECUTION FLOW TEST")
        print("="*80)

        # Step 1: Setup test data
        print("\n[SETUP] Preparing test environment...")

        # Get or create test strategy in database
        strategy_db = db.query(Strategy).filter(
            Strategy.name == "Test Execution Strategy"
        ).first()

        if not strategy_db:
            strategy_db = Strategy(
                name="Test Execution Strategy",
                description="Test strategy for full execution flow",
                parameters={
                    'stop_loss_pct': 0.05,
                    'take_profit_pct': 0.10
                },
                status="active"
            )
            db.add(strategy_db)
            db.commit()
            db.refresh(strategy_db)

        # Ensure strategy is active
        strategy_db.status = "active"
        strategy_db.consecutive_losses_today = 0
        db.commit()

        # Get test stock (AAPL)
        stock = db.query(Stock).filter(Stock.symbol == "AAPL").first()
        if not stock:
            print("❌ ERROR: AAPL not found in database.")
            print("Please add AAPL to your stocks table first.")
            return

        print(f"✓ Using strategy: {strategy_db.name} (ID: {strategy_db.id})")
        print(f"✓ Using stock: {stock.symbol} (ID: {stock.id})")

        # Create strategy instance for price calculations
        strategy = TestStrategy()

        # Step 2: Create test trading signal
        print("\n[STEP 1] Creating test BUY signal...")

        signal = TradingSignal(
            signal_type=SignalType.BUY,
            symbol="AAPL",
            timestamp=pd.Timestamp.now(),
            trigger_reason="Test signal for full execution flow validation",
            indicator_values={
                'test_indicator': 100.0,
                'confidence': 0.85
            },
            market_context={
                'test_mode': True,
                'description': 'Manual test execution'
            }
        )

        print(f"✓ Signal created: {signal.signal_type.value.upper()} {signal.symbol}")
        print(f"  Reason: {signal.trigger_reason}")

        # Step 3: Check portfolio state before execution
        print("\n[STEP 2] Checking portfolio state...")

        portfolio_value = position_sizer.get_portfolio_value()
        buying_power = position_sizer.get_available_cash()

        print(f"✓ Portfolio Value: ${portfolio_value:,.2f}")
        print(f"✓ Buying Power: ${buying_power:,.2f}")

        # Get current market price
        contract = client.create_stock_contract("AAPL")
        ticker = client.ib.reqMktData(contract, '', False, False)
        client.ib.sleep(2)

        current_price = ticker.last if ticker.last and ticker.last > 0 else (ticker.bid + ticker.ask) / 2
        client.ib.cancelMktData(contract)

        print(f"✓ Current AAPL Price: ${current_price:.2f}")

        # Calculate expected values
        stop_loss = strategy.calculate_stop_loss_price(current_price)
        take_profit = strategy.calculate_take_profit_price(current_price)

        print(f"✓ Expected Stop Loss: ${stop_loss:.2f} (5% below)")
        print(f"✓ Expected Take Profit: ${take_profit:.2f} (10% above)")

        # Step 4: Execute the signal
        print("\n[STEP 3] Executing signal through ExecutionEngine...")
        print("-" * 80)

        result = execution_engine.execute_signal(
            signal=signal,
            strategy=strategy,
            strategy_id=strategy_db.id
        )

        print("-" * 80)

        # Step 5: Analyze execution result
        print("\n[STEP 4] Analyzing execution result...")

        if not result.success:
            print(f"❌ EXECUTION FAILED: {result.error_message}")
            return

        print("✓ Execution successful!")
        print(f"\nCreated Records:")
        print(f"  Trade ID: {result.trade.id}")
        print(f"  Market Order ID: {result.market_order.id} (Broker: {result.market_order.broker_order_id})")
        print(f"  Stop-Loss Order ID: {result.stop_loss_order.id} (Broker: {result.stop_loss_order.broker_order_id})")
        print(f"  Take-Profit Order ID: {result.take_profit_order.id} (Broker: {result.take_profit_order.broker_order_id})")

        # Step 6: Verify trade details
        print(f"\nTrade Details:")
        print(f"  Symbol: {stock.symbol}")
        print(f"  Entry Price: ${result.trade.entry_price:.2f}")
        print(f"  Quantity: {result.trade.quantity} shares")
        print(f"  Position Value: ${float(result.trade.entry_price) * result.trade.quantity:,.2f}")
        print(f"  Stop Loss: ${result.trade.stop_loss:.2f}")
        print(f"  Take Profit: ${result.trade.take_profit:.2f}")
        print(f"  Status: {result.trade.status}")

        # Calculate position metrics
        position_value = float(result.trade.entry_price) * result.trade.quantity
        position_pct = (position_value / portfolio_value) * 100
        risk_per_share = float(result.trade.entry_price) - float(result.trade.stop_loss)
        risk_amount = risk_per_share * result.trade.quantity
        risk_pct = (risk_amount / portfolio_value) * 100

        print(f"\nPosition Metrics:")
        print(f"  Position Size: {position_pct:.2f}% of portfolio")
        print(f"  Risk Amount: ${risk_amount:.2f}")
        print(f"  Risk Percentage: {risk_pct:.2f}% of portfolio")
        print(f"  Risk:Reward Ratio: 1:{(float(result.trade.take_profit) - float(result.trade.entry_price)) / risk_per_share:.2f}")

        # Step 7: Verification checklist
        print("\n" + "="*80)
        print("VERIFICATION CHECKLIST")
        print("="*80)

        print("\n✓ Database Verification:")
        print(f"  [{'✓' if result.trade else '✗'}] Trade record created")
        print(f"  [{'✓' if result.market_order else '✗'}] Market order record created")
        print(f"  [{'✓' if result.stop_loss_order else '✗'}] Stop-loss order record created")
        print(f"  [{'✓' if result.take_profit_order else '✗'}] Take-profit order record created")

        print("\n✓ Risk Management Verification:")
        print(f"  [{'✓' if position_pct <= 20 else '✗'}] Position size ≤ 20% ({position_pct:.2f}%)")
        print(f"  [{'✓' if risk_pct <= 2.5 else '✗'}] Risk ≤ 2.5% ({risk_pct:.2f}%)")
        print(f"  [{'✓' if position_value <= buying_power else '✗'}] Position ≤ Buying power")

        print("\n📋 MANUAL VERIFICATION REQUIRED:")
        print("="*80)
        print("\nOpen IBKR TWS or IB Gateway and verify:")
        print("\n1. MARKET ORDER (should be FILLED):")
        print(f"   - Navigate to: Trade → Orders → Filled")
        print(f"   - Find Order ID: {result.market_order.broker_order_id}")
        print(f"   - Verify: BUY {result.trade.quantity} shares of AAPL")
        print(f"   - Verify: Order shows as 'Filled'")

        print("\n2. STOP-LOSS ORDER (should be ACTIVE):")
        print(f"   - Navigate to: Trade → Orders → Active")
        print(f"   - Find Order ID: {result.stop_loss_order.broker_order_id}")
        print(f"   - Verify: Order type is 'STP' (Stop)")
        print(f"   - Verify: Stop price is ${result.trade.stop_loss:.2f}")
        print(f"   - Verify: Action is 'SELL'")
        print(f"   - Verify: Quantity is {result.trade.quantity} shares")

        print("\n3. TAKE-PROFIT ORDER (should be ACTIVE):")
        print(f"   - Navigate to: Trade → Orders → Active")
        print(f"   - Find Order ID: {result.take_profit_order.broker_order_id}")
        print(f"   - Verify: Order type is 'LMT' (Limit)")
        print(f"   - Verify: Limit price is ${result.trade.take_profit:.2f}")
        print(f"   - Verify: Action is 'SELL'")
        print(f"   - Verify: Quantity is {result.trade.quantity} shares")

        print("\n4. BROKER-LEVEL PERSISTENCE TEST:")
        print(f"   - Close this script")
        print(f"   - Verify stop-loss and take-profit orders STILL VISIBLE in TWS")
        print(f"   - This confirms broker-level placement (survives app crash)")

        print("\n5. POSITION VERIFICATION:")
        print(f"   - Navigate to: Portfolio → Positions")
        print(f"   - Verify: {result.trade.quantity} shares of AAPL shown")
        print(f"   - Verify: Average cost matches entry price ${result.trade.entry_price:.2f}")

        print("\n" + "="*80)
        print("✓ FULL EXECUTION FLOW TEST COMPLETE")
        print("="*80)

        print("\n⚠️  IMPORTANT: Clean up test position when done:")
        print("   - Cancel the stop-loss and take-profit orders in TWS")
        print("   - Close the position manually if desired")
        print("   - Or let the stop/take-profit orders execute naturally")

    except Exception as e:
        print(f"\n❌ EXECUTION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()
        client.disconnect()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("⚠️  WARNING: This test will execute a REAL trade in your paper account!")
    print("="*80)
    print("\nPrerequisites:")
    print("  - IB Gateway/TWS running")
    print("  - Paper trading account active")
    print("  - Sufficient buying power (~$500+)")
    print("  - AAPL in database")
    print("  - Market hours or extended hours")

    response = input("\nContinue? (yes/no): ").strip().lower()

    if response in ['yes', 'y']:
        test_full_execution()
    else:
        print("\nTest cancelled.")
