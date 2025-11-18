"""Interactive Brokers API client using ib_insync."""
import logging
import asyncio
import time
from typing import Optional
from ib_insync import IB, Contract
from app.core.config import settings

logger = logging.getLogger(__name__)


class IBKRClient:
    """
    Wrapper for ib_insync.IB client to interact with Interactive Brokers API.

    Handles connection management, reconnection logic, and provides
    a clean interface for trading operations.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        client_id: Optional[int] = None
    ):
        """
        Initialize IBKR client.

        Args:
            host: IBKR Gateway/TWS host address (default from settings)
            port: IBKR Gateway/TWS port (default from settings)
            client_id: Unique client ID for this connection (default from settings)
        """
        self.host = host or settings.IBKR_HOST
        self.port = port or settings.IBKR_PORT
        self.client_id = client_id or settings.IBKR_CLIENT_ID

        # Initialize ib_insync IB instance
        self.ib = IB()

        # Connection state
        self._connected = False
        self._auto_reconnect = True
        self._reconnect_task = None

        logger.info(
            f"IBKRClient initialized - "
            f"host={self.host}, port={self.port}, client_id={self.client_id}"
        )

    def connect(self, max_retries: int = 3, retry_delay: int = 5) -> bool:
        """
        Connect to IBKR Gateway/TWS with retry logic.

        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Initial delay between retries in seconds (uses exponential backoff)

        Returns:
            bool: True if connected successfully, False otherwise

        Raises:
            ConnectionError: If all connection attempts fail
        """
        if self.is_connected:
            logger.info("Already connected to IBKR")
            return True

        logger.info(
            f"Attempting to connect to IBKR at {self.host}:{self.port} "
            f"with client_id={self.client_id}"
        )

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Connection attempt {attempt}/{max_retries}")

                # Attempt connection
                self.ib.connect(
                    host=self.host,
                    port=self.port,
                    clientId=self.client_id,
                    timeout=20
                )

                # Wait a moment for connection to stabilize
                time.sleep(1)

                if self.ib.isConnected():
                    self._connected = True

                    # Set up event handlers for connection monitoring
                    self.ib.connectedEvent += self._on_connected
                    self.ib.disconnectedEvent += self._on_disconnected
                    self.ib.errorEvent += self._on_error

                    logger.info(
                        f"Successfully connected to IBKR "
                        f"(attempt {attempt}/{max_retries})"
                    )
                    return True
                else:
                    logger.warning(
                        f"Connection reported success but isConnected() is False"
                    )

            except Exception as e:
                logger.error(
                    f"Connection attempt {attempt}/{max_retries} failed: {str(e)}"
                )

                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    error_msg = (
                        f"Failed to connect to IBKR after {max_retries} attempts. "
                        f"Please ensure IB Gateway/TWS is running and configured correctly."
                    )
                    logger.error(error_msg)
                    raise ConnectionError(error_msg)

        return False

    def disconnect(self):
        """
        Disconnect from IBKR Gateway/TWS.

        Cleanly closes the connection and stops auto-reconnect if enabled.
        """
        if not self._connected:
            logger.info("Already disconnected from IBKR")
            return

        logger.info("Disconnecting from IBKR...")

        # Disable auto-reconnect
        self._auto_reconnect = False

        try:
            # Remove event handlers
            self.ib.connectedEvent -= self._on_connected
            self.ib.disconnectedEvent -= self._on_disconnected
            self.ib.errorEvent -= self._on_error

            # Disconnect
            self.ib.disconnect()
            self._connected = False

            logger.info("Successfully disconnected from IBKR")

        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
            self._connected = False

    def reconnect(self, max_retries: int = 3) -> bool:
        """
        Reconnect to IBKR Gateway/TWS.

        Args:
            max_retries: Maximum number of reconnection attempts

        Returns:
            bool: True if reconnected successfully, False otherwise
        """
        logger.info("Attempting to reconnect to IBKR...")

        try:
            # Disconnect if still connected
            if self.is_connected:
                self.disconnect()

            # Re-enable auto-reconnect
            self._auto_reconnect = True

            # Attempt connection
            return self.connect(max_retries=max_retries)

        except Exception as e:
            logger.error(f"Reconnection failed: {str(e)}")
            return False

    def _on_connected(self):
        """Event handler called when connection is established."""
        logger.info("IBKR connection event: Connected")
        self._connected = True

    def _on_disconnected(self):
        """Event handler called when connection is lost."""
        logger.warning("IBKR connection event: Disconnected")
        self._connected = False

        # Attempt automatic reconnection if enabled
        if self._auto_reconnect:
            logger.info("Auto-reconnect enabled, attempting to reconnect...")
            try:
                # Wait a moment before attempting reconnection
                time.sleep(2)
                self.reconnect(max_retries=5)
            except Exception as e:
                logger.error(f"Auto-reconnect failed: {str(e)}")

    def _on_error(self, reqId, errorCode, errorString, contract):
        """
        Event handler for IBKR errors.

        Args:
            reqId: Request ID
            errorCode: Error code
            errorString: Error description
            contract: Related contract (if any)
        """
        # Error codes 2100-2110 are informational connection messages
        if 2100 <= errorCode <= 2110:
            logger.info(f"IBKR Info [{errorCode}]: {errorString}")
        # Error codes 1100-1102 are connectivity warnings
        elif 1100 <= errorCode <= 1102:
            logger.warning(f"IBKR Connectivity [{errorCode}]: {errorString}")
        else:
            logger.error(
                f"IBKR Error [{errorCode}]: {errorString} "
                f"(reqId={reqId}, contract={contract})"
            )

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to IBKR."""
        return self._connected and self.ib.isConnected()

    def get_account_summary(self) -> dict:
        """
        Get account summary information.

        Returns:
            dict: Account summary data
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to IBKR")

        account_values = self.ib.accountValues()
        summary = {}

        for value in account_values:
            if value.tag in ['NetLiquidation', 'TotalCashValue', 'BuyingPower']:
                summary[value.tag] = float(value.value)

        logger.debug(f"Account summary: {summary}")
        return summary

    def get_positions(self) -> list:
        """
        Get current positions from IBKR.

        Returns:
            list: List of Position objects
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to IBKR")

        positions = self.ib.positions()
        logger.debug(f"Retrieved {len(positions)} positions from IBKR")
        return positions

    def create_stock_contract(self, symbol: str, exchange: str = "SMART") -> Contract:
        """
        Create a stock contract for the given symbol.

        Args:
            symbol: Stock ticker symbol
            exchange: Exchange name (default: SMART for best execution)

        Returns:
            Contract: ib_insync Contract object
        """
        from ib_insync import Stock

        contract = Stock(symbol, exchange, 'USD')
        logger.debug(f"Created stock contract: {symbol} on {exchange}")
        return contract
