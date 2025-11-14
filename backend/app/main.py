"""Main FastAPI application entry point."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
import time
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger, get_logger
from app.api.endpoints import market_data, stocks

# Module logger
app_logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up Trading Application...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    yield
    # Shutdown
    logger.info("Shutting down Trading Application...")


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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Test with: wscat -c ws://localhost:8000/ws
    Or from browser console:
        const ws = new WebSocket('ws://localhost:8000/ws');
        ws.onmessage = (event) => console.log(event.data);
    """
    await websocket.accept()
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to Trading API WebSocket",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Echo loop for testing
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "echo",
                "received": data,
                "timestamp": datetime.utcnow().isoformat()
            })
    except WebSocketDisconnect:
        print("WebSocket disconnected")
