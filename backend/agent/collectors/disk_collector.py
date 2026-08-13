import psutil
from datetime import datetime
from agent.collectors.storage_analyzer import StorageAnalyzer


class DiskCollector:

    def __init__(self):
        self.analyzer = StorageAnalyzer(cache_ttl_seconds=120)

    def collect(self):
        disk = psutil.disk_usage("/")
        breakdown = self.analyzer.get_breakdown()

        return {
            "timestamp": datetime.now().isoformat(),
            "total_disk": disk.total,
            "used_disk": disk.used,
            "free_disk": disk.free,
            "disk_percent": disk.percent,
            "breakdown": breakdown,
        }