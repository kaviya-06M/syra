import psutil
from datetime import datetime


class DiskCollector:

    def collect(self):

        disk = psutil.disk_usage("/")

        return {
            "timestamp": datetime.now().isoformat(),
            "total_disk": disk.total,
            "used_disk": disk.used,
            "free_disk": disk.free,
            "disk_percent": disk.percent
        }