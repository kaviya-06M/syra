"""
/metrics routes - exposes the live system metrics collected every 5
seconds by the Background Agent (Step 4 of the SYRA pipeline), plus a
short rolling history so the frontend dashboard can plot trends.
"""

from collections import deque
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["metrics"])

# In-memory rolling buffer of the last N snapshots. Swap this for
# database.crud once the persistence layer is implemented.
_HISTORY_LIMIT = 500
_metrics_history = deque(maxlen=_HISTORY_LIMIT)


class MetricsSnapshot(BaseModel):
    timestamp: str
    cpu: dict
    memory: dict
    disk: dict
    network: dict
    processes: dict
    windows_events: list = []


def record_snapshot(snapshot: dict):
    """
    Called internally by agent.scheduler each collection cycle to push a
    fresh snapshot into the rolling buffer that these routes read from.
    """
    _metrics_history.append(snapshot)


@router.get("/current")
def get_current_metrics():
    """Returns the most recently collected snapshot."""
    if not _metrics_history:
        return {"message": "No metrics collected yet"}
    return _metrics_history[-1]


@router.get("/history")
def get_metrics_history(limit: int = 50):
    """Returns the last `limit` snapshots, most recent last."""
    limit = max(1, min(limit, _HISTORY_LIMIT))
    return list(_metrics_history)[-limit:]


@router.get("/summary")
def get_metrics_summary():
    """Quick averages over the current buffer, useful for a dashboard header."""
    if not _metrics_history:
        return {"message": "No metrics collected yet"}

    cpu_values = [m.get("cpu", {}).get("cpu_percent", 0) for m in _metrics_history]
    mem_values = [m.get("memory", {}).get("memory_percent", 0) for m in _metrics_history]
    disk_values = [m.get("disk", {}).get("disk_percent", 0) for m in _metrics_history]

    return {
        "sample_count": len(_metrics_history),
        "avg_cpu_percent": round(sum(cpu_values) / len(cpu_values), 2),
        "avg_memory_percent": round(sum(mem_values) / len(mem_values), 2),
        "avg_disk_percent": round(sum(disk_values) / len(disk_values), 2),
        "generated_at": datetime.now().isoformat()
    }


@router.get("/storage")
def get_storage_breakdown(refresh: bool = False):
    """Returns detailed folder-level breakdown and disk statistics."""
    from agent.collectors.storage_analyzer import StorageAnalyzer
    import psutil

    disk = psutil.disk_usage("/")
    analyzer = StorageAnalyzer(cache_ttl_seconds=120)
    breakdown = analyzer.get_breakdown(force_refresh=refresh)

    return {
        "total_disk": disk.total,
        "used_disk": disk.used,
        "free_disk": disk.free,
        "disk_percent": disk.percent,
        "breakdown": breakdown,
        "timestamp": datetime.now().isoformat()
    }
