"""Tests for market hours detection."""
import pytest
from datetime import datetime, time
import pytz

from app.services.data.market_hours import (
    is_market_open,
    is_weekday,
    is_market_holiday,
    is_pre_market,
    is_after_hours,
    get_market_status,
    MARKET_OPEN_TIME,
    MARKET_CLOSE_TIME
)

ET = pytz.timezone("America/New_York")


@pytest.mark.unit
def test_is_weekday():
    """Test weekday detection."""
    # Monday, Jan 13, 2025
    monday = ET.localize(datetime(2025, 1, 13, 12, 0))
    assert is_weekday(monday) is True

    # Saturday, Jan 11, 2025
    saturday = ET.localize(datetime(2025, 1, 11, 12, 0))
    assert is_weekday(saturday) is False

    # Sunday, Jan 12, 2025
    sunday = ET.localize(datetime(2025, 1, 12, 12, 0))
    assert is_weekday(sunday) is False


@pytest.mark.unit
def test_is_market_holiday():
    """Test market holiday detection."""
    # New Year's Day 2025
    new_years = ET.localize(datetime(2025, 1, 1, 12, 0))
    assert is_market_holiday(new_years) is True

    # Regular trading day
    regular_day = ET.localize(datetime(2025, 1, 15, 12, 0))
    assert is_market_holiday(regular_day) is False


@pytest.mark.unit
def test_is_market_open_during_hours():
    """Test market open detection during trading hours."""
    # Wednesday at 2 PM ET (market open)
    market_open = ET.localize(datetime(2025, 1, 15, 14, 0))
    assert is_market_open(market_open) is True


@pytest.mark.unit
def test_is_market_open_before_hours():
    """Test market closed before 9:30 AM."""
    # Wednesday at 8 AM ET (before market open)
    before_open = ET.localize(datetime(2025, 1, 15, 8, 0))
    assert is_market_open(before_open) is False


@pytest.mark.unit
def test_is_market_open_after_hours():
    """Test market closed after 4:00 PM."""
    # Wednesday at 5 PM ET (after market close)
    after_close = ET.localize(datetime(2025, 1, 15, 17, 0))
    assert is_market_open(after_close) is False


@pytest.mark.unit
def test_is_market_open_weekend():
    """Test market closed on weekends."""
    # Saturday at noon
    saturday = ET.localize(datetime(2025, 1, 11, 12, 0))
    assert is_market_open(saturday) is False


@pytest.mark.unit
def test_is_pre_market():
    """Test pre-market hours detection."""
    # Wednesday at 7 AM ET (pre-market)
    pre_market_time = ET.localize(datetime(2025, 1, 15, 7, 0))
    assert is_pre_market(pre_market_time) is True

    # Wednesday at 10 AM ET (regular hours)
    regular_time = ET.localize(datetime(2025, 1, 15, 10, 0))
    assert is_pre_market(regular_time) is False


@pytest.mark.unit
def test_is_after_hours():
    """Test after-hours detection."""
    # Wednesday at 5 PM ET (after-hours)
    after_hours_time = ET.localize(datetime(2025, 1, 15, 17, 0))
    assert is_after_hours(after_hours_time) is True

    # Wednesday at 3 PM ET (regular hours)
    regular_time = ET.localize(datetime(2025, 1, 15, 15, 0))
    assert is_after_hours(regular_time) is False


@pytest.mark.unit
def test_get_market_status():
    """Test comprehensive market status."""
    # Wednesday at 2 PM ET (market open)
    market_time = ET.localize(datetime(2025, 1, 15, 14, 0))
    status = get_market_status(market_time)

    assert status["is_weekday"] is True
    assert status["is_market_open"] is True
    assert status["session"] == "regular"
    assert "next_open" in status
    assert "next_close" in status


@pytest.mark.unit
def test_market_status_weekend():
    """Test market status on weekend."""
    # Saturday
    saturday = ET.localize(datetime(2025, 1, 11, 12, 0))
    status = get_market_status(saturday)

    assert status["is_weekday"] is False
    assert status["is_market_open"] is False
    assert status["session"] == "closed"
