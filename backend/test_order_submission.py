"""Test order submission to IBKR paper account."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.trading.ibkr_client import IBKRClient
from app.services.trading.order_service import OrderService
from app.core.config import settings
from app.database import SessionLocal
from app.models.stock import Stock

def test_market_order():
    """Test submitting a market order for a small quantity."""

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
        # Get or create AAPL stock
        stock = db.query(Stock).filter(Stock.symbol == "AAPL").first()
        if not stock:
            print("ERROR: AAPL not in database. Please add it first.")
            return

        print("\n" + "="*60)
        print("MARKET ORDER TEST")
        print("="*60)
        print(f"Symbol: AAPL")
        print(f"Quantity: 1 share")
        print(f"Action: BUY")
        print("-"*60)

        # Submit market order for 1 share of AAPL
        order = order_service.submit_market_order(
            symbol="AAPL",
            quantity=1,
            action="BUY",
            stock_id=stock.id
        )

        print(f"✓ Order submitted successfully!")
        print(f"Order ID: {order.id}")
        print(f"Broker Order ID: {order.broker_order_id}")
        print(f"Status: {order.status}")
        print("="*60)

        print("\n📋 NEXT STEPS:")
        print("1. Open IBKR TWS or IB Gateway")
        print("2. Navigate to: Trade → Orders")
        print(f"3. Look for order ID: {order.broker_order_id}")
        print("4. Verify order shows as 'Filled' or 'Submitted'")
        print("5. Check the database orders table for this order")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

    finally:
        db.close()
        client.disconnect()

if __name__ == "__main__":
    test_market_order()
