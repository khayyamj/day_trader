"""Tests for rate limiter."""
import pytest
import time
from app.core.rate_limiter import RateLimiter


@pytest.mark.unit
def test_rate_limiter_initialization():
    """Test rate limiter initializes correctly."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_day=100)

    assert limiter.calls_per_minute == 10
    assert limiter.calls_per_day == 100
    assert limiter.minute_tokens == 10
    assert limiter.day_tokens == 100


@pytest.mark.unit
def test_rate_limiter_can_proceed():
    """Test can_proceed method."""
    limiter = RateLimiter(calls_per_minute=5, calls_per_day=100)

    # Should allow first call
    assert limiter.can_proceed() is True

    # Consume all tokens
    for _ in range(5):
        limiter.acquire(wait=False)

    # Should deny when no tokens
    assert limiter.can_proceed() is False


@pytest.mark.unit
def test_rate_limiter_acquire():
    """Test acquiring tokens."""
    limiter = RateLimiter(calls_per_minute=5, calls_per_day=100)

    # Acquire 5 tokens
    for i in range(5):
        result = limiter.acquire(wait=False)
        assert result is True
        # Use approximate comparison due to token refill
        assert limiter.minute_tokens < 5 - i
        assert limiter.minute_tokens >= 0

    # 6th attempt should fail (no wait)
    result = limiter.acquire(wait=False)
    assert result is False


@pytest.mark.unit
def test_rate_limiter_daily_limit():
    """Test daily limit enforcement."""
    limiter = RateLimiter(calls_per_minute=10, calls_per_day=5)

    # Consume daily limit
    for _ in range(5):
        limiter.acquire(wait=False)

    assert limiter.day_tokens == 0

    # Should raise error when wait=True
    with pytest.raises(RuntimeError, match="Daily rate limit exceeded"):
        limiter.acquire(wait=True)


@pytest.mark.unit
def test_rate_limiter_token_refill():
    """Test that tokens refill over time."""
    limiter = RateLimiter(calls_per_minute=60, calls_per_day=1000)  # 1 token/second

    # Consume a token
    limiter.acquire(wait=False)
    assert limiter.minute_tokens < 60

    # Wait 1 second
    time.sleep(1.1)

    # Should have refilled
    limiter._refill_tokens()
    assert limiter.minute_tokens > 59  # Close to 60


@pytest.mark.unit
def test_rate_limiter_get_status():
    """Test get_status method."""
    limiter = RateLimiter(calls_per_minute=8, calls_per_day=800)

    status = limiter.get_status()

    assert "calls_per_minute" in status
    assert "calls_per_day" in status
    assert "tokens_remaining_minute" in status
    assert "tokens_remaining_day" in status
    assert status["calls_per_minute"] == 8
    assert status["calls_per_day"] == 800
