"""Market information API endpoints."""
from fastapi import APIRouter

from app.services.data.market_hours import get_market_status
from app.core.logging import get_logger

logger = get_logger("market_api")

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/status")
async def market_status():
    """
    Get current market status.

    Returns comprehensive market information including:
    - Whether market is currently open
    - Current trading session (regular/pre-market/after-hours/closed)
    - Next market open/close times
    - Holiday and weekend detection

    Example response:
    ```json
    {
        "current_time_et": "2025-01-15T14:30:00-05:00",
        "is_weekday": true,
        "is_holiday": false,
        "is_market_open": true,
        "is_pre_market": false,
        "is_after_hours": false,
        "session": "regular",
        "next_open": "2025-01-15T09:30:00-05:00",
        "next_close": "2025-01-15T16:00:00-05:00"
    }
    ```
    """
    logger.info("Market status requested")
    status = get_market_status()
    return status
