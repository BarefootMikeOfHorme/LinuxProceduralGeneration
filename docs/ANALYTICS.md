# VaultMind Forge - Analytics & Telemetry

VaultMind Forge includes privacy-first analytics and optional telemetry to help you understand usage patterns and improve your workflows.

---

## Overview

### Local Analytics (Default: ON)
- **Storage**: SQLite database on your machine (`./data/analytics.db`)
- **Privacy**: 100% private, never leaves your system
- **Purpose**: Track workflow execution, node usage, errors
- **Data Retention**: Automatically cleaned up after 90 days

### Remote Telemetry (Default: OFF)
- **Storage**: Optional remote endpoint
- **Privacy**: Fully anonymized, no PII collected
- **Purpose**: Help improve VaultMind Forge (opt-in only)
- **Data**: Aggregated metrics only (node counts, success rates)

---

## Configuration

### Enable/Disable Analytics

```env
# .env file
VAULTMIND_ANALYTICS_ENABLED=true  # Enable local analytics
VAULTMIND_ANALYTICS_DB=./data/analytics.db  # Database location
```

### Enable Telemetry (Optional)

```env
# .env file
VAULTMIND_TELEMETRY_ENABLED=true  # Opt-in to telemetry
VAULTMIND_TELEMETRY_ENDPOINT=https://telemetry.example.com/v1/events
```

---

## What Data is Collected?

### Local Analytics
- Workflow execution times
- Node types used
- Success/failure rates
- Error codes and categories
- Performance metrics

**NOT collected**: File paths, API keys, personal data

### Remote Telemetry (if enabled)
- Anonymized device ID (machine hash)
- Workflow node count (not content)
- Average execution times
- Error categories (not messages)
- Platform information (OS, Python version)

**NOT collected**: Workflow content, file paths, API keys, IP addresses, usernames

---

## API Endpoints

### Get Analytics Status
```bash
GET /api/analytics/status
```

Returns:
```json
{
  "analytics": {
    "enabled": true,
    "database": "./data/analytics.db"
  },
  "telemetry": {
    "enabled": false,
    "endpoint": null
  }
}
```

### Get Workflow Statistics
```bash
GET /api/analytics/stats?days=7
```

Returns:
```json
{
  "total_workflows": 42,
  "completed": 38,
  "failed": 4,
  "success_rate": 90.48,
  "avg_duration_ms": 1234.5,
  "period_days": 7
}
```

### Get Node Usage Statistics
```bash
GET /api/analytics/nodes?limit=10
```

Returns:
```json
{
  "nodes": [
    {
      "node_type": "text_input",
      "execution_count": 120,
      "success_count": 118,
      "failure_count": 2,
      "avg_duration_ms": 5.3,
      "success_rate": 98.33,
      "last_used": "2025-12-10 15:30:22"
    },
    ...
  ]
}
```

### Get Error Summary
```bash
GET /api/analytics/errors?days=7
```

Returns:
```json
{
  "errors": [
    {
      "error_code": "WORKFLOW_VALIDATION_ERROR",
      "error_message": "Missing required input connection",
      "occurrence_count": 5,
      "first_seen": "2025-12-08 10:00:00",
      "last_seen": "2025-12-10 14:30:00"
    },
    ...
  ]
}
```

### Cleanup Old Data
```bash
POST /api/analytics/cleanup?days=90
```

Returns:
```json
{
  "message": "Cleaned up 1234 old records",
  "deleted_count": 1234
}
```

---

## Database Schema

### Events Table
Stores all analytics events with timestamps.

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
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
```

### Workflow Metrics Table
Aggregated workflow statistics.

```sql
CREATE TABLE workflow_metrics (
    id INTEGER PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    node_count INTEGER,
    edge_count INTEGER,
    total_duration_ms REAL,
    status TEXT,
    error_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Node Stats Table
Per-node-type usage statistics.

```sql
CREATE TABLE node_stats (
    id INTEGER PRIMARY KEY,
    node_type TEXT NOT NULL,
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    avg_duration_ms REAL,
    last_used DATETIME,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Error Log Table
Error occurrence tracking.

```sql
CREATE TABLE error_log (
    id INTEGER PRIMARY KEY,
    error_code TEXT NOT NULL,
    error_message TEXT,
    stack_trace TEXT,
    context TEXT,
    occurrence_count INTEGER DEFAULT 1,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

---

## Privacy Guarantees

### What We Do:
✅ Store all analytics locally by default
✅ Allow you to disable analytics completely
✅ Anonymize all telemetry data
✅ Provide full control over data retention
✅ Auto-cleanup old data (90 days default)

### What We Don't Do:
❌ Collect personal information
❌ Track individual users
❌ Store API keys or credentials
❌ Send data without consent
❌ Use third-party analytics services (unless you opt-in)

---

## Programmatic Access

### Python API

```python
from backend.analytics import (
    track_workflow_started,
    track_workflow_completed,
    track_node_executed,
    get_analytics_store
)

# Track events
track_workflow_started("workflow-123", node_count=5)
track_workflow_completed("workflow-123", duration_ms=1500)
track_node_executed("node-1", "text_input", duration_ms=10)

# Query analytics
analytics = get_analytics_store()
stats = analytics.get_workflow_stats(days=7)
print(f"Success rate: {stats['success_rate']}%")
```

### Telemetry API (Optional)

```python
from backend.telemetry import get_telemetry_service
import asyncio

async def send_telemetry():
    telemetry = get_telemetry_service()

    # Send anonymized metrics
    await telemetry.track_workflow_execution(
        node_count=5,
        duration_ms=1500,
        success=True
    )

asyncio.run(send_telemetry())
```

---

## Compliance

VaultMind Forge analytics are designed to comply with:
- **GDPR**: No personal data collected
- **CCPA**: Full transparency and control
- **SOC 2**: Local-first data storage
- **Self-hosted**: You own all your data

---

## FAQ

**Q: Can I disable analytics?**
A: Yes, set `VAULTMIND_ANALYTICS_ENABLED=false` in your `.env` file.

**Q: Where is analytics data stored?**
A: In a SQLite database at `./data/analytics.db` (configurable).

**Q: Is telemetry enabled by default?**
A: No, telemetry is disabled by default and requires explicit opt-in.

**Q: What happens to my data if I uninstall?**
A: All analytics data is stored locally in `./data/`. Delete this directory to remove all analytics data.

**Q: Can I export my analytics data?**
A: Yes, the SQLite database can be queried directly or exported using standard SQLite tools.

**Q: How long is data retained?**
A: Data is automatically cleaned up after 90 days. This is configurable using the cleanup API.

---

## Support

For questions about analytics and privacy:
- **Documentation**: [/docs](/docs)
- **Issues**: [GitHub Issues](https://github.com/BarefootMikeOfHorme/LinuxProceduralGeneration/issues)
- **Email**: barefoot.mike.of.horme@gmail.com
