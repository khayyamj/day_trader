"""Main FastAPI application entry point."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
import time
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger, get_logger
from app.api.endpoints import market_data, stocks, scheduler, market
from app.services.data.realtime_service import connection_manager
from app.services.data.scheduler import data_scheduler
from app.db.session import SessionLocal

# Module logger
app_logger = get_logger("main")

# Global background task
price_streaming_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global price_streaming_task

    # Startup
    logger.info("Starting up Trading Application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Start scheduler (skip in test environment)
    if settings.ENVIRONMENT.lower() != "test":
        data_scheduler.start()
        logger.info("Data scheduler started")
    else:
        logger.info("Test mode: Scheduler disabled")

    # Start price streaming in background
    # Commented out for now - will be enabled when API key is configured
    # from app.services.data.realtime_service import RealtimeService
    # db = SessionLocal()
    # service = RealtimeService(db)
    # price_streaming_task = asyncio.create_task(service.start_price_streaming())
    # logger.info("Price streaming task started")

    yield

    # Shutdown
    logger.info("Shutting down Trading Application...")

    # Stop scheduler
    data_scheduler.shutdown()
    logger.info("Data scheduler stopped")

    # Stop price streaming
    # if price_streaming_task:
    #     price_streaming_task.cancel()
    #     logger.info("Price streaming task stopped")


app = FastAPI(
    title="Trading Application API",
    description="API for algorithmic trading with MACD/RSI strategy",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests and responses."""
    start_time = time.time()

    # Log request
    app_logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown"
        }
    )

    # Process request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        app_logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s"
            }
        )

        # Add custom header
        response.headers["X-Process-Time"] = str(process_time)
        return response

    except Exception as e:
        process_time = time.time() - start_time
        app_logger.error(
            f"Request failed: {request.method} {request.url.path} - {str(e)}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "process_time": f"{process_time:.3f}s"
            }
        )
        raise


# Include API routers
app.include_router(stocks.router, prefix="/api")
app.include_router(market_data.router, prefix="/api")
app.include_router(scheduler.router, prefix="/api")
app.include_router(market.router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "trading-api",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Trading Application API",
        "docs": "/docs",
        "health": "/health"
    }


@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    """
    WebSocket endpoint for real-time price updates.

    Clients connect here to receive price updates every 30 seconds.

    Test with browser console:
        const ws = new WebSocket('ws://localhost:8000/ws/prices');
        ws.onmessage = (event) => console.log(JSON.parse(event.data));

    Message format:
    {
        "type": "price_update",
        "timestamp": "2025-01-15T12:00:00",
        "prices": {
            "AAPL": {"symbol": "AAPL", "close": "150.25", ...},
            "MSFT": {"symbol": "MSFT", "close": "380.50", ...}
        }
    }
    """
    await connection_manager.connect(websocket)

    try:
        # Send welcome message
        await connection_manager.send_personal(websocket, {
            "type": "connection",
            "message": "Connected to price streaming",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep connection alive
        while True:
            # Wait for client messages (ping/pong to keep alive)
            try:
                data = await websocket.receive_text()
                # Echo back for testing
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"WebSocket error: {e}")

    finally:
        connection_manager.disconnect(websocket)


@app.websocket("/ws")
async def websocket_legacy(websocket: WebSocket):
    """
    Legacy WebSocket endpoint for testing.

    Use /ws/prices for price updates.
    """
    await websocket.accept()
    try:
        await websocket.send_json({
            "type": "info",
            "message": "This is a test endpoint. Use /ws/prices for real-time price updates.",
            "timestamp": datetime.utcnow().isoformat()
        })

        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "echo",
                "received": data,
                "timestamp": datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        logger.info("Legacy WebSocket disconnected")
