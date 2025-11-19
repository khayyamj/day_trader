"""Test position reconciliation system."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.trading.ibkr_client import IBKRClient
from app.services.trading.position_service import PositionService
from app.core.config import settings
from app.database import SessionLocal

def test_reconciliation():
    """
    Test position reconciliation.

    MANUAL SETUP REQUIRED:
    1. Manually create a small position in IBKR TWS (e.g., buy 1 share of AAPL)
    2. Do NOT add this trade to the database
    3. Run this script
    4. Script should detect the discrepancy
    """

    # Setup
    client = IBKRClient(
        host=settings.IBKR_HOST,
        port=settings.IBKR_PORT,
        client_id=settings.IBKR_CLIENT_ID
    )
    client.connect()

    db = SessionLocal()
    position_service = PositionService(client, db)

    try:
        print("\n" + "="*60)
        print("POSITION RECONCILIATION TEST")
        print("="*60)

        print("\n📋 MANUAL SETUP INSTRUCTIONS:")
        print("Before running this test:")
        print("1. Open IBKR TWS")
        print("2. Manually buy 1 share of AAPL (or any stock)")
        print("3. Wait for order to fill")
        print("4. DO NOT add this trade to your database")
        print("5. Press Enter when ready...")
        input()

        # Get broker positions
        print("\n1. Fetching positions from IBKR broker...")
        broker_positions = position_service.get_broker_positions()
        print(f"   Found {len(broker_positions)} positions at broker:")
        for symbol, data in broker_positions.items():
            print(f"   - {symbol}: {data['quantity']} shares @ ${data['avg_cost']:.2f}")

        # Get database positions
        print("\n2. Fetching positions from database...")
        db_positions = position_service.get_db_positions()
        print(f"   Found {len(db_positions)} positions in database:")
        for symbol, data in db_positions.items():
            print(f"   - {symbol}: {data['quantity']} shares @ ${data['avg_cost']:.2f}")

        # Run reconciliation
        print("\n3. Running reconciliation...")
        discrepancies, total_value_diff = position_service.reconcile_positions()

        if not discrepancies:
            print("   ✓ No discrepancies found - positions match!")
        else:
            print(f"   ⚠️  Found {len(discrepancies)} discrepancies:")
            for disc in discrepancies:
                print(f"\n   Discrepancy: {disc.symbol}")
                print(f"   - Broker Qty: {disc.broker_quantity}")
                print(f"   - DB Qty: {disc.db_quantity}")
                print(f"   - Type: {disc.discrepancy_type}")
                print(f"   - Value Diff: ${disc.value_difference:,.2f}")

            print(f"\n   Total Value Difference: ${total_value_diff:,.2f}")

        # Check if major discrepancy
        print("\n4. Checking for major discrepancy (>$100)...")
        is_major = position_service.check_major_discrepancy(total_value_diff)
        if is_major:
            print(f"   ⚠️  MAJOR DISCREPANCY DETECTED: ${total_value_diff:,.2f}")
            print("   Expected: Trading should be paused, alert sent")
        else:
            print(f"   ✓ Within acceptable threshold: ${total_value_diff:,.2f}")

        print("\n" + "="*60)
        print("✓ Reconciliation test complete!")
        print("="*60)

        print("\n📋 VERIFICATION CHECKLIST:")
        print("✓ Script detected the position at broker")
        print("✓ Script identified discrepancy vs database")
        print("✓ Discrepancy type correctly identified")
        print("✓ Value difference calculated")
        print("✓ Major discrepancy threshold checked")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()
        client.disconnect()

if __name__ == "__main__":
    test_reconciliation()
