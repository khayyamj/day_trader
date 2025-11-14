"""Rate limiter using token bucket algorithm."""
import time
import asyncio
from typing import Optional
from app.core.logging import get_logger

logger = get_logger("rate_limiter")


class RateLimiter:
    """
    Token bucket rate limiter.

    Implements both per-minute and per-day rate limits.
    """

    def __init__(
        self,
        calls_per_minute: int = 8,
        calls_per_day: int = 800
    ):
        """
        Initialize rate limiter.

        Args:
            calls_per_minute: Maximum calls allowed per minute
            calls_per_day: Maximum calls allowed per day
        """
        self.calls_per_minute = calls_per_minute
        self.calls_per_day = calls_per_day

        # Per-minute tracking
        self.minute_tokens = calls_per_minute
        self.minute_last_update = time.time()

        # Per-day tracking
        self.day_tokens = calls_per_day
        self.day_last_reset = time.time()

        logger.info(
            f"RateLimiter initialized: {calls_per_minute} calls/min, {calls_per_day} calls/day"
        )

    def _refill_tokens(self):
        """Refill tokens based on time elapsed."""
        now = time.time()

        # Refill per-minute tokens (1 token per 60/calls_per_minute seconds)
        time_since_update = now - self.minute_last_update
        tokens_to_add = time_since_update * (self.calls_per_minute / 60.0)
        self.minute_tokens = min(
            self.calls_per_minute,
            self.minute_tokens + tokens_to_add
        )
        self.minute_last_update = now

        # Reset daily tokens if 24 hours passed
        if now - self.day_last_reset >= 86400:  # 24 hours in seconds
            logger.info("Daily rate limit reset")
            self.day_tokens = self.calls_per_day
            self.day_last_reset = now

    def can_proceed(self) -> bool:
        """
        Check if request can proceed within rate limits.

        Returns:
            True if request is allowed, False otherwise
        """
        self._refill_tokens()
        return self.minute_tokens >= 1 and self.day_tokens >= 1

    def acquire(self, wait: bool = True) -> bool:
        """
        Acquire permission to make an API call.

        Args:
            wait: If True, block until token available; if False, return immediately

        Returns:
            True if acquired, False if denied (only when wait=False)

        Raises:
            RuntimeError: If daily limit exceeded and wait=True
        """
        self._refill_tokens()

        # Check daily limit first
        if self.day_tokens < 1:
            error_msg = f"Daily rate limit exceeded ({self.calls_per_day} calls/day)"
            logger.error(error_msg)
            if wait:
                raise RuntimeError(error_msg)
            return False

        # Wait for per-minute tokens if needed
        if wait:
            while self.minute_tokens < 1:
                wait_time = (60.0 / self.calls_per_minute)
                logger.warning(f"Rate limit: waiting {wait_time:.1f}s for next token")
                time.sleep(wait_time)
                self._refill_tokens()

        if self.minute_tokens < 1:
            return False

        # Consume tokens
        self.minute_tokens -= 1
        self.day_tokens -= 1

        logger.debug(
            f"Token acquired. Remaining: {self.minute_tokens:.1f}/min, {self.day_tokens}/day"
        )
        return True

    async def acquire_async(self, wait: bool = True) -> bool:
        """
        Async version of acquire().

        Args:
            wait: If True, block until token available; if False, return immediately

        Returns:
            True if acquired, False if denied
        """
        self._refill_tokens()

        if self.day_tokens < 1:
            error_msg = f"Daily rate limit exceeded ({self.calls_per_day} calls/day)"
            logger.error(error_msg)
            if wait:
                raise RuntimeError(error_msg)
            return False

        if wait:
            while self.minute_tokens < 1:
                wait_time = (60.0 / self.calls_per_minute)
                logger.warning(f"Rate limit: waiting {wait_time:.1f}s for next token")
                await asyncio.sleep(wait_time)
                self._refill_tokens()

        if self.minute_tokens < 1:
            return False

        self.minute_tokens -= 1
        self.day_tokens -= 1

        logger.debug(
            f"Token acquired (async). Remaining: {self.minute_tokens:.1f}/min, {self.day_tokens}/day"
        )
        return True

    def get_status(self) -> dict:
        """
        Get current rate limit status.

        Returns:
            Dictionary with remaining calls and reset times
        """
        self._refill_tokens()
        return {
            "calls_per_minute": self.calls_per_minute,
            "calls_per_day": self.calls_per_day,
            "tokens_remaining_minute": int(self.minute_tokens),
            "tokens_remaining_day": self.day_tokens,
            "minute_resets_in": 60.0 - (time.time() - self.minute_last_update),
            "day_resets_in": 86400 - (time.time() - self.day_last_reset)
        }


# Global rate limiter instance for Twelve Data API
twelve_data_limiter = RateLimiter(calls_per_minute=8, calls_per_day=800)
