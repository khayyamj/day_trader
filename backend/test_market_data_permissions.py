"""Check market data permissions and subscription status."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.trading.ibkr_client import IBKRClient
from app.core.config import settings
from ib_insync import Stock

def test_permissions():
    """Check what market data permissions we have."""

    client = IBKRClient(
        host=settings.IBKR_HOST,
        port=settings.IBKR_PORT,
        client_id=settings.IBKR_CLIENT_ID
    )

    try:
        client.connect()
        print("\n" + "="*60)
        print("MARKET DATA PERMISSIONS CHECK")
        print("="*60)

        # Get managed accounts
        print(f"\nAccount: {client.ib.managedAccounts()}")

        # Try to get market data and capture errors
        print("\n1. Attempting to request market data for AAPL...")
        contract = Stock("AAPL", "SMART", "USD")

        # Set up error handler to capture permission errors
        errors = []

        def error_handler(reqId, errorCode, errorString, contract):
            errors.append({
                'reqId': reqId,
                'code': errorCode,
                'message': errorString
            })
            print(f"   Error {errorCode}: {errorString}")

        client.ib.errorEvent += error_handler

        ticker = client.ib.reqMktData(contract, '', False, False)
        client.ib.sleep(5)  # Wait longer for data or error

        print(f"\n2. Ticker data received:")
        print(f"   Last: {ticker.last}")
        print(f"   Delayed: {ticker.delayed}")
        print(f"   DelayedLast: {ticker.delayedLast}")
        print(f"   DelayedBid: {ticker.delayedBid}")
        print(f"   DelayedAsk: {ticker.delayedAsk}")

        # Check for specific error codes
        print(f"\n3. Analyzing errors:")
        if not errors:
            print("   ✓ No errors - market data request accepted")
        else:
            for err in errors:
                if err['code'] == 354:
                    print(f"   ✗ Error 354: No market data permissions")
                    print("     → You need to subscribe to market data")
                elif err['code'] == 162:
                    print(f"   ✗ Error 162: Multiple connections detected")
                    print("     → Close other TWS/Gateway instances")
                elif err['code'] == 10167:
                    print(f"   ✗ Error 10167: No market data during competing live session")
                    print("     → Close other IBKR sessions")
                else:
                    print(f"   ⚠ Error {err['code']}: {err['message']}")

        client.ib.cancelMktData(contract)

        # Try requesting delayed data explicitly
        print(f"\n4. Requesting DELAYED market data explicitly...")
        ticker2 = client.ib.reqMktData(contract, '', False, False)
        # Request delayed data
        client.ib.reqMarketDataType(3)  # 3 = delayed data, 1 = live, 2 = frozen
        client.ib.sleep(5)

        print(f"   DelayedLast: {ticker2.delayedLast}")
        print(f"   DelayedBid: {ticker2.delayedBid}")
        print(f"   DelayedAsk: {ticker2.delayedAsk}")
        print(f"   Last: {ticker2.last}")

        client.ib.cancelMktData(contract)

        print("\n" + "="*60)
        print("DIAGNOSIS")
        print("="*60)

        has_any_data = (
            ticker.last and not str(ticker.last) == 'nan' or
            ticker.delayedLast and not str(ticker.delayedLast) == 'nan' or
            ticker2.delayedLast and not str(ticker2.delayedLast) == 'nan'
        )

        if has_any_data:
            print("✓ Market data is working!")
        else:
            print("✗ No market data access")
            print("\nPossible causes:")
            print("1. Subscriptions not activated yet (can take 15-30 min)")
            print("2. Paper trading account restrictions")
            print("3. Need to accept data agreements in Account Management")
            print("4. Multiple TWS/Gateway sessions running")
            print("\nNext steps:")
            print("1. Log into: https://www.interactivebrokers.com")
            print("2. Go to: Account Management → Settings → User Settings")
            print("3. Click: Market Data Subscriptions")
            print("4. Verify subscriptions show 'Active' status")
            print("5. Check: Data Agreements are all signed")

        print("="*60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        client.disconnect()

if __name__ == "__main__":
    test_permissions()
