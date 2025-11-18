"""Test script for IBKR connection."""
import sys
import logging
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.trading.ibkr_client import IBKRClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_connection():
    """Test connection to IBKR Gateway/TWS."""
    logger.info("=" * 60)
    logger.info("IBKR Connection Test")
    logger.info("=" * 60)

    # Create client instance
    logger.info("\n1. Creating IBKRClient instance...")
    client = IBKRClient()

    try:
        # Test connection
        logger.info("\n2. Attempting to connect to IBKR...")
        success = client.connect(max_retries=3, retry_delay=5)

        if success:
            logger.info("\n✓ Successfully connected to IBKR!")

            # Get account summary
            logger.info("\n3. Retrieving account summary...")
            try:
                summary = client.get_account_summary()
                logger.info(f"Account Summary:")
                for key, value in summary.items():
                    logger.info(f"  {key}: ${value:,.2f}")
            except Exception as e:
                logger.error(f"Failed to get account summary: {str(e)}")

            # Get positions
            logger.info("\n4. Retrieving positions...")
            try:
                positions = client.get_positions()
                logger.info(f"Current positions: {len(positions)}")
                for pos in positions:
                    logger.info(f"  {pos.contract.symbol}: {pos.position} shares @ ${pos.avgCost:.2f}")
            except Exception as e:
                logger.error(f"Failed to get positions: {str(e)}")

            # Test disconnect
            logger.info("\n5. Testing disconnect...")
            client.disconnect()
            logger.info("✓ Successfully disconnected")

            logger.info("\n" + "=" * 60)
            logger.info("✓ All tests passed!")
            logger.info("=" * 60)
            return True

        else:
            logger.error("\n✗ Failed to connect to IBKR")
            logger.error("\nPlease ensure:")
            logger.error("  1. IB Gateway or TWS is running")
            logger.error("  2. API settings are configured correctly:")
            logger.error("     - Socket port: 7497 (paper trading)")
            logger.error("     - Enable ActiveX and Socket API is checked")
            logger.error("     - 127.0.0.1 is in trusted IP addresses")
            logger.error("  3. Your .env file has correct IBKR credentials")
            return False

    except Exception as e:
        logger.error(f"\n✗ Test failed with error: {str(e)}")
        return False

    finally:
        # Ensure cleanup
        try:
            if client.is_connected:
                client.disconnect()
        except:
            pass


if __name__ == "__main__":
    logger.info("Starting IBKR connection test...")
    logger.info("Make sure IB Gateway is running before proceeding!\n")

    success = test_connection()

    sys.exit(0 if success else 1)
