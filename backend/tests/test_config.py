"""Tests for configuration."""
import pytest
from app.core.config import Settings


@pytest.mark.unit
def test_settings_load_defaults():
    """Test that settings load with default values."""
    settings = Settings()

    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is True
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None
    assert settings.BACKEND_CORS_ORIGINS is not None


@pytest.mark.unit
def test_settings_environment_properties():
    """Test environment detection properties."""
    settings = Settings(ENVIRONMENT="development")
    assert settings.is_development is True
    assert settings.is_production is False

    settings = Settings(ENVIRONMENT="production")
    assert settings.is_development is False
    assert settings.is_production is True


@pytest.mark.unit
def test_settings_validation_development():
    """Test that validation works in development mode."""
    settings = Settings()

    # In development, Twelve Data key is required
    with pytest.raises(ValueError, match="TWELVE_DATA_API_KEY"):
        settings.validate_required_keys("development")


@pytest.mark.unit
def test_settings_validation_production():
    """Test that validation requires more keys in production."""
    settings = Settings()

    # In production, both Twelve Data and IBKR keys are required
    with pytest.raises(ValueError):
        settings.validate_required_keys("production")


@pytest.mark.unit
def test_cors_origins_parsing():
    """Test that CORS origins can be parsed from string."""
    # Test JSON string parsing
    settings = Settings(BACKEND_CORS_ORIGINS='["http://localhost:3000"]')
    assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS

    # Test comma-separated parsing
    settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000,http://localhost:8000")
    assert len(settings.BACKEND_CORS_ORIGINS) == 2
