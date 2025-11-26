"""API endpoints for querying strategy events."""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.strategy_event import StrategyEvent
from app.db.database import get_db

router = APIRouter()


@router.get("/events")
def get_events(
    strategy_id: Optional[int] = Query(None, description="Filter by strategy ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    hours: int = Query(24, description="Get events from last N hours"),
    limit: int = Query(100, description="Maximum number of events to return"),
    db: Session = Depends(get_db)
):
    """
    Get recent strategy events with optional filters.

    Args:
        strategy_id: Filter events by strategy ID
        event_type: Filter by event type (TRADE, SIGNAL, ORDER, RISK, ERROR, etc.)
        severity: Filter by severity (INFO, WARNING, ERROR, CRITICAL)
        hours: Get events from last N hours (default: 24)
        limit: Maximum number of events (default: 100)
        db: Database session

    Returns:
        List of strategy events matching the filters
    """
    # Calculate time threshold
    time_threshold = datetime.utcnow() - timedelta(hours=hours)

    # Build query
    query = db.query(StrategyEvent).filter(StrategyEvent.timestamp >= time_threshold)

    # Apply filters
    if strategy_id:
        query = query.filter(StrategyEvent.strategy_id == strategy_id)
    if event_type:
        query = query.filter(StrategyEvent.event_type == event_type)
    if severity:
        query = query.filter(StrategyEvent.severity == severity)

    # Order by most recent first and apply limit
    events = query.order_by(desc(StrategyEvent.timestamp)).limit(limit).all()

    return {
        "events": [
            {
                "id": event.id,
                "strategy_id": event.strategy_id,
                "event_type": event.event_type,
                "severity": event.severity,
                "timestamp": event.timestamp.isoformat(),
                "message": event.message,
                "meta": event.meta or {}
            }
            for event in events
        ],
        "count": len(events),
        "filters": {
            "strategy_id": strategy_id,
            "event_type": event_type,
            "severity": severity,
            "hours": hours
        }
    }


@router.get("/events/summary")
def get_events_summary(
    strategy_id: Optional[int] = Query(None, description="Filter by strategy ID"),
    hours: int = Query(24, description="Get events from last N hours"),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics of events.

    Args:
        strategy_id: Filter events by strategy ID
        hours: Get events from last N hours (default: 24)
        db: Database session

    Returns:
        Summary statistics including counts by event type and severity
    """
    # Calculate time threshold
    time_threshold = datetime.utcnow() - timedelta(hours=hours)

    # Build query
    query = db.query(StrategyEvent).filter(StrategyEvent.timestamp >= time_threshold)

    if strategy_id:
        query = query.filter(StrategyEvent.strategy_id == strategy_id)

    events = query.all()

    # Calculate summaries
    event_type_counts = {}
    severity_counts = {}

    for event in events:
        event_type_counts[event.event_type] = event_type_counts.get(event.event_type, 0) + 1
        severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1

    return {
        "total_events": len(events),
        "event_type_counts": event_type_counts,
        "severity_counts": severity_counts,
        "time_range_hours": hours,
        "strategy_id": strategy_id
    }
