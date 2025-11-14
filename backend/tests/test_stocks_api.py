"""Tests for stock watchlist API endpoints."""
import pytest
from app.models.stock import Stock


@pytest.mark.unit
def test_list_stocks_empty(client):
    """Test listing stocks when watchlist is empty."""
    response = client.get("/api/stocks/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["stocks"] == []


@pytest.mark.unit
def test_list_stocks_with_data(client, db_session):
    """Test listing stocks with data in watchlist."""
    # Add stocks to database
    stock1 = Stock(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ")
    stock2 = Stock(symbol="MSFT", name="Microsoft Corp.", exchange="NASDAQ")

    db_session.add(stock1)
    db_session.add(stock2)
    db_session.commit()

    response = client.get("/api/stocks/")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["stocks"]) == 2

    symbols = {stock["symbol"] for stock in data["stocks"]}
    assert "AAPL" in symbols
    assert "MSFT" in symbols


@pytest.mark.unit
def test_get_stock_found(client, db_session):
    """Test getting a specific stock."""
    stock = Stock(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ")
    db_session.add(stock)
    db_session.commit()

    response = client.get("/api/stocks/AAPL")

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["name"] == "Apple Inc."


@pytest.mark.unit
def test_get_stock_not_found(client):
    """Test getting non-existent stock."""
    response = client.get("/api/stocks/INVALID")

    assert response.status_code == 404
    assert "not in watchlist" in response.json()["detail"]


@pytest.mark.unit
def test_delete_stock(client, db_session):
    """Test deleting a stock from watchlist."""
    stock = Stock(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ")
    db_session.add(stock)
    db_session.commit()

    response = client.delete("/api/stocks/AAPL")

    assert response.status_code == 204

    # Verify deleted
    remaining = db_session.query(Stock).filter(Stock.symbol == "AAPL").first()
    assert remaining is None


@pytest.mark.unit
def test_delete_stock_not_found(client):
    """Test deleting non-existent stock."""
    response = client.delete("/api/stocks/INVALID")

    assert response.status_code == 404
