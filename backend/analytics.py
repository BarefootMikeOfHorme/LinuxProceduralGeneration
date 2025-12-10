"""
VaultMind Forge - Analytics & Telemetry System

Privacy-first analytics for tracking workflow execution, node usage,
performance metrics, and error rates. Designed for self-hosted deployments
with full user control over data collection.
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import sqlite3
from contextlib import contextmanager

# Analytics configuration
ANALYTICS_ENABLED = os.getenv("VAULTMIND_ANALYTICS_ENABLED", "true").lower() == "true"
ANALYTICS_DB_PATH = os.getenv("VAULTMIND_ANALYTICS_DB", "./data/analytics.db")
TELEMETRY_ENABLED = os.getenv("VAULTMIND_TELEMETRY_ENABLED", "false").lower() == "true"
TELEMETRY_ENDPOINT = os.getenv("VAULTMIND_TELEMETRY_ENDPOINT", "")

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Types of analytics events"""
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    NODE_EXECUTED = "node.executed"
    NODE_FAILED = "node.failed"
    API_REQUEST = "api.request"
    ERROR_OCCURRED = "error.occurred"
    PERFORMANCE_METRIC = "performance.metric"
    USER_ACTION = "user.action"


@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""
    event_type: EventType
    timestamp: float
    workflow_id: Optional[str] = None
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    duration_ms: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        if self.metadata:
            data['metadata'] = json.dumps(self.metadata)
        return data


class AnalyticsStore:
    """Local SQLite storage for analytics data"""

    def __init__(self, db_path: str = ANALYTICS_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _initialize_db(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    workflow_id TEXT,
                    node_id TEXT,
                    node_type TEXT,
                    duration_ms REAL,
                    error_code TEXT,
                    error_message TEXT,
                    metadata TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Workflow metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    node_count INTEGER,
                    edge_count INTEGER,
                    total_duration_ms REAL,
                    status TEXT,
                    error_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Node usage statistics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS node_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_type TEXT NOT NULL,
                    execution_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    avg_duration_ms REAL,
                    last_used DATETIME,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Error tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_code TEXT NOT NULL,
                    error_message TEXT,
                    stack_trace TEXT,
                    context TEXT,
                    occurrence_count INTEGER DEFAULT 1,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_workflow ON events(workflow_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_node_stats_type ON node_stats(node_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_code ON error_log(error_code)")

            conn.commit()
            logger.info(f"Analytics database initialized at {self.db_path}")

    def record_event(self, event: AnalyticsEvent):
        """Record an analytics event"""
        if not ANALYTICS_ENABLED:
            return

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                event_dict = event.to_dict()

                cursor.execute("""
                    INSERT INTO events (
                        event_type, timestamp, workflow_id, node_id, node_type,
                        duration_ms, error_code, error_message, metadata, user_id, session_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_dict['event_type'],
                    event_dict['timestamp'],
                    event_dict.get('workflow_id'),
                    event_dict.get('node_id'),
                    event_dict.get('node_type'),
                    event_dict.get('duration_ms'),
                    event_dict.get('error_code'),
                    event_dict.get('error_message'),
                    event_dict.get('metadata'),
                    event_dict.get('user_id', 'anonymous'),
                    event_dict.get('session_id'),
                ))

                conn.commit()

                # Update aggregated statistics
                self._update_node_stats(event, conn)
                self._update_error_stats(event, conn)

        except Exception as e:
            logger.error(f"Failed to record analytics event: {e}")

    def _update_node_stats(self, event: AnalyticsEvent, conn):
        """Update node usage statistics"""
        if event.node_type and event.event_type in [EventType.NODE_EXECUTED, EventType.NODE_FAILED]:
            cursor = conn.cursor()

            # Check if node type exists
            cursor.execute("SELECT id FROM node_stats WHERE node_type = ?", (event.node_type,))
            row = cursor.fetchone()

            if row:
                # Update existing stats
                cursor.execute("""
                    UPDATE node_stats
                    SET execution_count = execution_count + 1,
                        success_count = success_count + CASE WHEN ? = 'node.executed' THEN 1 ELSE 0 END,
                        failure_count = failure_count + CASE WHEN ? = 'node.failed' THEN 1 ELSE 0 END,
                        avg_duration_ms = (
                            (avg_duration_ms * execution_count + COALESCE(?, 0)) / (execution_count + 1)
                        ),
                        last_used = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE node_type = ?
                """, (event.event_type.value, event.event_type.value, event.duration_ms, event.node_type))
            else:
                # Insert new stats
                cursor.execute("""
                    INSERT INTO node_stats (
                        node_type, execution_count, success_count, failure_count,
                        avg_duration_ms, last_used
                    ) VALUES (?, 1, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    event.node_type,
                    1 if event.event_type == EventType.NODE_EXECUTED else 0,
                    1 if event.event_type == EventType.NODE_FAILED else 0,
                    event.duration_ms or 0
                ))

            conn.commit()

    def _update_error_stats(self, event: AnalyticsEvent, conn):
        """Update error occurrence statistics"""
        if event.error_code:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO error_log (error_code, error_message, occurrence_count, first_seen, last_seen)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(error_code) DO UPDATE SET
                    occurrence_count = occurrence_count + 1,
                    last_seen = CURRENT_TIMESTAMP,
                    error_message = COALESCE(excluded.error_message, error_message)
            """, (event.error_code, event.error_message))

            conn.commit()

    def get_workflow_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cutoff_time = time.time() - (days * 86400)

            # Total workflows
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN event_type = 'workflow.completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN event_type = 'workflow.failed' THEN 1 END) as failed,
                    AVG(duration_ms) as avg_duration
                FROM events
                WHERE event_type IN ('workflow.completed', 'workflow.failed')
                AND timestamp > ?
            """, (cutoff_time,))

            row = cursor.fetchone()

            return {
                "total_workflows": row["total"] or 0,
                "completed": row["completed"] or 0,
                "failed": row["failed"] or 0,
                "success_rate": (row["completed"] / row["total"] * 100) if row["total"] > 0 else 0,
                "avg_duration_ms": row["avg_duration"] or 0,
                "period_days": days
            }

    def get_node_usage(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most used node types"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    node_type,
                    execution_count,
                    success_count,
                    failure_count,
                    avg_duration_ms,
                    ROUND(success_count * 100.0 / execution_count, 2) as success_rate,
                    last_used
                FROM node_stats
                ORDER BY execution_count DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_error_summary(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get error occurrence summary"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cutoff_time = datetime.now() - timedelta(days=days)

            cursor.execute("""
                SELECT
                    error_code,
                    error_message,
                    occurrence_count,
                    first_seen,
                    last_seen
                FROM error_log
                WHERE last_seen > ?
                ORDER BY occurrence_count DESC
                LIMIT 20
            """, (cutoff_time,))

            return [dict(row) for row in cursor.fetchall()]

    def get_performance_trends(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance metric trends"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cutoff_time = time.time() - (hours * 3600)

            cursor.execute("""
                SELECT
                    timestamp,
                    metric_value,
                    metadata
                FROM performance_metrics
                WHERE metric_name = ? AND timestamp > ?
                ORDER BY timestamp ASC
            """, (metric_name, cutoff_time))

            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_data(self, days: int = 90):
        """Clean up analytics data older than specified days"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cutoff_time = time.time() - (days * 86400)

            cursor.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_time,))
            cursor.execute("DELETE FROM performance_metrics WHERE timestamp < ?", (cutoff_time,))

            deleted_count = cursor.rowcount
            conn.commit()

            logger.info(f"Cleaned up {deleted_count} old analytics records")
            return deleted_count


# Global analytics store instance
_analytics_store: Optional[AnalyticsStore] = None


def get_analytics_store() -> AnalyticsStore:
    """Get or create the global analytics store"""
    global _analytics_store
    if _analytics_store is None:
        _analytics_store = AnalyticsStore()
    return _analytics_store


# Convenience functions
def track_workflow_started(workflow_id: str, node_count: int = 0, session_id: Optional[str] = None):
    """Track workflow execution start"""
    if not ANALYTICS_ENABLED:
        return

    event = AnalyticsEvent(
        event_type=EventType.WORKFLOW_STARTED,
        timestamp=time.time(),
        workflow_id=workflow_id,
        session_id=session_id,
        metadata={"node_count": node_count}
    )
    get_analytics_store().record_event(event)


def track_workflow_completed(workflow_id: str, duration_ms: float, session_id: Optional[str] = None):
    """Track workflow execution completion"""
    if not ANALYTICS_ENABLED:
        return

    event = AnalyticsEvent(
        event_type=EventType.WORKFLOW_COMPLETED,
        timestamp=time.time(),
        workflow_id=workflow_id,
        duration_ms=duration_ms,
        session_id=session_id
    )
    get_analytics_store().record_event(event)


def track_workflow_failed(workflow_id: str, error_code: str, error_message: str, session_id: Optional[str] = None):
    """Track workflow execution failure"""
    if not ANALYTICS_ENABLED:
        return

    event = AnalyticsEvent(
        event_type=EventType.WORKFLOW_FAILED,
        timestamp=time.time(),
        workflow_id=workflow_id,
        error_code=error_code,
        error_message=error_message,
        session_id=session_id
    )
    get_analytics_store().record_event(event)


def track_node_executed(node_id: str, node_type: str, duration_ms: float, workflow_id: Optional[str] = None):
    """Track individual node execution"""
    if not ANALYTICS_ENABLED:
        return

    event = AnalyticsEvent(
        event_type=EventType.NODE_EXECUTED,
        timestamp=time.time(),
        workflow_id=workflow_id,
        node_id=node_id,
        node_type=node_type,
        duration_ms=duration_ms
    )
    get_analytics_store().record_event(event)


def track_node_failed(node_id: str, node_type: str, error_code: str, error_message: str, workflow_id: Optional[str] = None):
    """Track node execution failure"""
    if not ANALYTICS_ENABLED:
        return

    event = AnalyticsEvent(
        event_type=EventType.NODE_FAILED,
        timestamp=time.time(),
        workflow_id=workflow_id,
        node_id=node_id,
        node_type=node_type,
        error_code=error_code,
        error_message=error_message
    )
    get_analytics_store().record_event(event)


def track_error(error_code: str, error_message: str, metadata: Optional[Dict] = None):
    """Track general error occurrence"""
    if not ANALYTICS_ENABLED:
        return

    event = AnalyticsEvent(
        event_type=EventType.ERROR_OCCURRED,
        timestamp=time.time(),
        error_code=error_code,
        error_message=error_message,
        metadata=metadata
    )
    get_analytics_store().record_event(event)


def track_performance_metric(metric_name: str, metric_value: float, metadata: Optional[Dict] = None):
    """Track performance metric"""
    if not ANALYTICS_ENABLED:
        return

    event = AnalyticsEvent(
        event_type=EventType.PERFORMANCE_METRIC,
        timestamp=time.time(),
        metadata={
            "metric_name": metric_name,
            "metric_value": metric_value,
            **(metadata or {})
        }
    )
    get_analytics_store().record_event(event)
