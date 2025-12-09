"""
VaultMind Forge - Persistence Layer
SQLite-backed storage for workflows and executions
Replaces in-memory dicts with proper database storage
"""

from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from abc import ABC, abstractmethod
from contextlib import contextmanager

# Import centralized logging
from backend.logging_config import get_logger

logger = get_logger("persistence")


class PersistenceError(Exception):
    """Raised when persistence operations fail"""
    pass


class Store(ABC):
    """Abstract base class for all stores"""

    @abstractmethod
    async def save(self, id: str, data: dict) -> None:
        """Save data by ID"""
        pass

    @abstractmethod
    async def load(self, id: str) -> Optional[dict]:
        """Load data by ID"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete data by ID"""
        pass

    @abstractmethod
    async def list_all(self) -> List[dict]:
        """List all stored items"""
        pass

    @abstractmethod
    async def exists(self, id: str) -> bool:
        """Check if ID exists"""
        pass


class SQLiteStore(Store):
    """
    SQLite-backed persistent storage.

    Features:
    - Thread-safe with connection pooling
    - JSON serialization for complex data
    - Automatic schema creation
    - Transaction support
    """

    def __init__(self, db_path: Path, table_name: str):
        """
        Initialize SQLite store.

        Args:
            db_path: Path to SQLite database file
            table_name: Name of table to use for this store
        """
        self.db_path = Path(db_path)
        self.table_name = table_name

        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema
        self._init_schema()

        logger.info(f"Initialized SQLite store: {table_name} at {db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self):
        """Create table if it doesn't exist"""
        with self._get_connection() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create index on timestamps for faster queries
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created
                ON {self.table_name}(created_at)
            """)

            conn.commit()

    async def save(self, id: str, data: dict) -> None:
        """
        Save data to database.

        Args:
            id: Unique identifier
            data: Data to save (will be JSON serialized)

        Raises:
            PersistenceError: If save fails
        """
        try:
            now = datetime.utcnow().isoformat()
            json_data = json.dumps(data)

            with self._get_connection() as conn:
                # Check if exists
                cursor = conn.execute(
                    f"SELECT id FROM {self.table_name} WHERE id = ?",
                    (id,)
                )
                exists = cursor.fetchone() is not None

                if exists:
                    # Update existing
                    conn.execute(
                        f"""
                        UPDATE {self.table_name}
                        SET data = ?, updated_at = ?
                        WHERE id = ?
                        """,
                        (json_data, now, id)
                    )
                else:
                    # Insert new
                    conn.execute(
                        f"""
                        INSERT INTO {self.table_name} (id, data, created_at, updated_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (id, json_data, now, now)
                    )

                conn.commit()

        except Exception as e:
            error_msg = f"Failed to save {id} to {self.table_name}: {str(e)}"
            logger.error(error_msg)
            raise PersistenceError(error_msg) from e

    async def load(self, id: str) -> Optional[dict]:
        """
        Load data from database.

        Args:
            id: Unique identifier

        Returns:
            Dict with data or None if not found

        Raises:
            PersistenceError: If load fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    f"SELECT data FROM {self.table_name} WHERE id = ?",
                    (id,)
                )
                row = cursor.fetchone()

                if row is None:
                    return None

                return json.loads(row['data'])

        except Exception as e:
            error_msg = f"Failed to load {id} from {self.table_name}: {str(e)}"
            logger.error(error_msg)
            raise PersistenceError(error_msg) from e

    async def delete(self, id: str) -> bool:
        """
        Delete data from database.

        Args:
            id: Unique identifier

        Returns:
            True if deleted, False if not found

        Raises:
            PersistenceError: If delete fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    f"DELETE FROM {self.table_name} WHERE id = ?",
                    (id,)
                )
                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            error_msg = f"Failed to delete {id} from {self.table_name}: {str(e)}"
            logger.error(error_msg)
            raise PersistenceError(error_msg) from e

    async def list_all(self) -> List[dict]:
        """
        List all stored items.

        Returns:
            List of all data dicts

        Raises:
            PersistenceError: If list fails
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    f"SELECT data FROM {self.table_name} ORDER BY created_at DESC"
                )

                results = []
                for row in cursor.fetchall():
                    results.append(json.loads(row['data']))

                return results

        except Exception as e:
            error_msg = f"Failed to list from {self.table_name}: {str(e)}"
            logger.error(error_msg)
            raise PersistenceError(error_msg) from e

    async def exists(self, id: str) -> bool:
        """
        Check if ID exists.

        Args:
            id: Unique identifier

        Returns:
            True if exists, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    f"SELECT 1 FROM {self.table_name} WHERE id = ? LIMIT 1",
                    (id,)
                )
                return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"Failed to check existence of {id}: {str(e)}")
            return False

    async def count(self) -> int:
        """Get count of stored items"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    f"SELECT COUNT(*) as count FROM {self.table_name}"
                )
                return cursor.fetchone()['count']

        except Exception as e:
            logger.error(f"Failed to count items: {str(e)}")
            return 0

    async def clear_all(self) -> int:
        """
        Clear all data from store (use with caution!).

        Returns:
            Number of items deleted
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(f"DELETE FROM {self.table_name}")
                conn.commit()
                return cursor.rowcount

        except Exception as e:
            error_msg = f"Failed to clear {self.table_name}: {str(e)}"
            logger.error(error_msg)
            raise PersistenceError(error_msg) from e


class WorkflowStore(SQLiteStore):
    """Store for workflow definitions"""

    def __init__(self, db_path: Path):
        super().__init__(db_path, "workflows")


class ExecutionStore(SQLiteStore):
    """
    Store for workflow executions.

    Additional features:
    - Status tracking (pending, running, completed, failed)
    - Progress tracking
    """

    def __init__(self, db_path: Path):
        super().__init__(db_path, "executions")

    def _init_schema(self):
        """Create executions table with additional fields"""
        with self._get_connection() as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)

            # Create indexes
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_status
                ON {self.table_name}(status)
            """)

            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_created
                ON {self.table_name}(created_at)
            """)

            conn.commit()

    async def save(self, id: str, data: dict) -> None:
        """Save execution with status and progress tracking"""
        try:
            now = datetime.utcnow().isoformat()
            json_data = json.dumps(data)

            # Extract status and progress from data
            status = data.get('status', 'pending')
            progress = int(data.get('percentage', 0))
            completed_at = now if status in ('completed', 'failed') else None

            with self._get_connection() as conn:
                cursor = conn.execute(
                    f"SELECT id FROM {self.table_name} WHERE id = ?",
                    (id,)
                )
                exists = cursor.fetchone() is not None

                if exists:
                    conn.execute(
                        f"""
                        UPDATE {self.table_name}
                        SET data = ?, status = ?, progress = ?,
                            updated_at = ?, completed_at = ?
                        WHERE id = ?
                        """,
                        (json_data, status, progress, now, completed_at, id)
                    )
                else:
                    conn.execute(
                        f"""
                        INSERT INTO {self.table_name}
                        (id, data, status, progress, created_at, updated_at, completed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (id, json_data, status, progress, now, now, completed_at)
                    )

                conn.commit()

        except Exception as e:
            error_msg = f"Failed to save execution {id}: {str(e)}"
            logger.error(error_msg)
            raise PersistenceError(error_msg) from e

    async def get_by_status(self, status: str) -> List[dict]:
        """Get all executions with a specific status"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    f"SELECT data FROM {self.table_name} WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )

                results = []
                for row in cursor.fetchall():
                    results.append(json.loads(row['data']))

                return results

        except Exception as e:
            logger.error(f"Failed to get executions by status: {str(e)}")
            return []


class PersistenceManager:
    """
    Central manager for all persistence stores.

    Provides unified access to workflows and executions stores.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize persistence manager.

        Args:
            db_path: Path to SQLite database (default: ./data/vaultmind.db)
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "vaultmind.db"

        self.db_path = Path(db_path)

        # Initialize stores
        self.workflows = WorkflowStore(self.db_path)
        self.executions = ExecutionStore(self.db_path)

        logger.info(f"Persistence manager initialized with database: {self.db_path}")

    async def get_stats(self) -> dict:
        """Get storage statistics"""
        return {
            "database_path": str(self.db_path),
            "database_size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0,
            "workflow_count": await self.workflows.count(),
            "execution_count": await self.executions.count(),
        }


# Global instance (lazy initialized)
_persistence_manager: Optional[PersistenceManager] = None


def get_persistence() -> PersistenceManager:
    """
    Get global persistence manager instance.

    Returns:
        PersistenceManager singleton
    """
    global _persistence_manager

    if _persistence_manager is None:
        _persistence_manager = PersistenceManager()

    return _persistence_manager


__all__ = [
    "Store",
    "SQLiteStore",
    "WorkflowStore",
    "ExecutionStore",
    "PersistenceManager",
    "PersistenceError",
    "get_persistence",
]
