"""Main FastAPI application entry point."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
from datetime import datetime

# Will be imported once config is set up
# from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting up Trading Application...")
    yield
    # Shutdown
    print("Shutting down Trading Application...")


app = FastAPI(
    title="Trading Application API",
    description="API for algorithmic trading with MACD/RSI strategy",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
origins = [
    "http://localhost:3000",  # React default
    "http://localhost:8000",  # FastAPI default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
