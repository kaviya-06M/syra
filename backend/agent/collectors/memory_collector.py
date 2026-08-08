import psutil
from datetime import datetime


class MemoryCollector:

    def collect(self):
        memory = psutil.virtual_memory()

        return {
            "timestamp": datetime.now().isoformat(),
            "total_memory": memory.total,
            "available_memory": memory.available,
            "used_memory": memory.used,
            "memory_percent": memory.percent
        }