import psutil
from datetime import datetime


class CPUCollector:

    def collect(self):
        freq = psutil.cpu_freq()
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "cpu_frequency": freq.current if freq else None
        }