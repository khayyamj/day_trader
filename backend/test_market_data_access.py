"""Test what market data we can actually access with current subscription."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.trading.ibkr_client import IBKRClient
from app.core.config import settings
from ib_insync import Stock

def test_market_data():
    """Test various methods of getting market data."""

    client = IBKRClient(
        host=settings.IBKR_HOST,
        port=settings.IBKR_PORT,
        client_id=settings.IBKR_CLIENT_ID
    )

    try:
        client.connect()
        print("\n" + "="*60)
        print("MARKET DATA ACCESS TEST")
        print("="*60)

        symbol = "AAPL"
        contract = Stock(symbol, "SMART", "USD")

        # Test 1: Streaming market data
        print(f"\n1. Testing streaming market data for {symbol}...")
        ticker = client.ib.reqMktData(contract, '', False, False)
        client.ib.sleep(3)  # Wait for data

        print(f"   Last: {ticker.last}")
        print(f"   Bid: {ticker.bid}")
        print(f"   Ask: {ticker.ask}")
        print(f"   Close: {ticker.close}")
        print(f"   Market Price: {ticker.marketPrice()}")
        print(f"   Has delayed data: {ticker.halted}")

        client.ib.cancelMktData(contract)

        # Test 2: Snapshot request
        print(f"\n2. Testing snapshot data for {symbol}...")
        snapshot = client.ib.reqMktData(contract, '', True, False)  # snapshot=True
        client.ib.sleep(3)

        print(f"   Last: {snapshot.last}")
        print(f"   Bid: {snapshot.bid}")
        print(f"   Ask: {snapshot.ask}")
        print(f"   Close: {snapshot.close}")
        print(f"   Market Price: {snapshot.marketPrice()}")

        client.ib.cancelMktData(contract)

        # Test 3: Contract details (always available)
        print(f"\n3. Testing contract details for {symbol}...")
        details = client.ib.reqContractDetails(contract)
        if details:
            print(f"   Contract found: {details[0].contract.symbol}")
            print(f"   Exchange: {details[0].contract.primaryExchange}")
            print(f"   Currency: {details[0].contract.currency}")

        # Test 4: Historical data (might work with delayed data)
        print(f"\n4. Testing historical data for {symbol}...")
        bars = client.ib.reqHistoricalData(
            contract,
            endDateTime='',
            durationStr='1 D',
            barSizeSetting='1 hour',
            whatToShow='TRADES',
            useRTH=True
        )

        if bars:
            latest_bar = bars[-1]
            print(f"   Latest bar close: ${latest_bar.close}")
            print(f"   Bar time: {latest_bar.date}")
            print(f"   ✓ Historical data available!")
        else:
            print(f"   ✗ No historical data available")

        print("\n" + "="*60)
        print("SUBSCRIPTION ASSESSMENT")
        print("="*60)

        # Assess what's available
        has_realtime = ticker.last and ticker.last > 0
        has_snapshot = snapshot.last and snapshot.last > 0
        has_historical = len(bars) > 0 if bars else False

        if has_realtime:
            print("✓ You have REAL-TIME market data access")
            print("  → Can test stop-loss orders with live prices")
        elif has_snapshot:
            print("⚠ You have SNAPSHOT market data access")
            print("  → Limited quotes per month, can test orders")
        elif has_historical:
            print("⚠ You have DELAYED/HISTORICAL data access only")
            print("  → Can use historical close prices for testing")
        else:
            print("✗ No market data access detected")
            print("  → Need to subscribe to market data")

        print("="*60)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        client.disconnect()

if __name__ == "__main__":
    test_market_data()
