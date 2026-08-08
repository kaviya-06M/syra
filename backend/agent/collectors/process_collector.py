import psutil
from datetime import datetime


class ProcessCollector:

    def collect(self):

        processes = []

        for process in psutil.process_iter(
                ['pid', 'name', 'cpu_percent', 'memory_percent']):

            try:

                processes.append({

                    "pid": process.info["pid"],
                    "name": process.info["name"],
                    "cpu": process.info["cpu_percent"],
                    "memory": round(process.info["memory_percent"] or 0.0, 2)

                })

            except Exception:
                continue

        processes = sorted(
            processes,
            key=lambda x: x["memory"],
            reverse=True
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "top_processes": processes[:10]
        }