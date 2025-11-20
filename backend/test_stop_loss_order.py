"""Test stop-loss order submission to verify broker-level placement."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.trading.ibkr_client import IBKRClient
from app.services.trading.order_service import OrderService
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.stock import Stock

def test_stop_loss_order():
    """Test submitting a stop-loss order at broker level."""

    # Setup
    client = IBKRClient(
        host=settings.IBKR_HOST,
        port=settings.IBKR_PORT,
        client_id=settings.IBKR_CLIENT_ID
    )
    client.connect()

    db = SessionLocal()
    order_service = OrderService(client, db)

    try:
        # Get AAPL stock
        stock = db.query(Stock).filter(Stock.symbol == "AAPL").first()
        if not stock:
            print("ERROR: AAPL not in database. Please add it first.")
            return

        # Get current price
        contract = client.create_stock_contract("AAPL")
        ticker = client.ib.reqMktData(contract, '', False, False)
        client.ib.sleep(2)

        current_price = ticker.last if ticker.last else (ticker.bid + ticker.ask) / 2
        stop_price = current_price * 0.95  # 5% below current price

        client.ib.cancelMktData(contract)

        print("\n" + "="*60)
        print("STOP-LOSS ORDER TEST")
        print("="*60)
        print(f"Symbol: AAPL")
        print(f"Current Price: ${current_price:.2f}")
        print(f"Stop Price: ${stop_price:.2f} (5% below)")
        print(f"Quantity: 1 share")
        print("-"*60)

        # Submit stop-loss order
        order = order_service.submit_stop_loss_order(
            symbol="AAPL",
            quantity=1,
            stop_price=stop_price,
            stock_id=stock.id
        )

        print(f"✓ Stop-loss order submitted successfully!")
        print(f"Order ID: {order.id}")
        print(f"Broker Order ID: {order.broker_order_id}")
        print(f"Status: {order.status}")
        print("="*60)

        print("\n📋 CRITICAL VERIFICATION:")
        print("1. Open IBKR TWS or IB Gateway")
        print("2. Navigate to: Trade → Orders")
        print(f"3. Find order ID: {order.broker_order_id}")
        print("4. Verify order type shows as 'STP' (Stop Order)")
        print(f"5. Verify stop price is ${stop_price:.2f}")
        print("6. ⚠️  IMPORTANT: Order should persist at broker level")
        print("   - Close this script")
        print("   - Order should still be visible in TWS")
        print("   - This proves broker-level placement (survives app crash)")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

    finally:
        db.close()
        client.disconnect()

if __name__ == "__main__":
    test_stop_loss_order()
