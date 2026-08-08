from datetime import datetime


class DataCleaner:
    """
    Cleans a single raw event dict produced by EventGenerator
    (cpu, memory, disk, network, processes, windows_events)
    before it goes into feature engineering.
    """

    def clean(self, event):
        cleaned = {
            "timestamp": self._safe_timestamp(event.get("timestamp")),
            "cpu": self._clean_cpu(event.get("cpu", {})),
            "memory": self._clean_memory(event.get("memory", {})),
            "disk": self._clean_disk(event.get("disk", {})),
            "network": self._clean_network(event.get("network", {})),
            "processes": self._clean_processes(event.get("processes", {})),
            "windows_events": event.get("windows_events") or []
        }
        return cleaned

    def _safe_timestamp(self, ts):
        if not ts:
            return datetime.now().isoformat()
        return ts

    def _clean_cpu(self, cpu):
        return {
            "cpu_percent": self._clamp(cpu.get("cpu_percent"), 0, 100, default=0.0),
            "physical_cores": cpu.get("physical_cores") or 1,
            "logical_cores": cpu.get("logical_cores") or 1,
            "cpu_frequency": cpu.get("cpu_frequency") or 0.0
        }

    def _clean_memory(self, memory):
        return {
            "total_memory": memory.get("total_memory") or 0,
            "available_memory": memory.get("available_memory") or 0,
            "used_memory": memory.get("used_memory") or 0,
            "memory_percent": self._clamp(memory.get("memory_percent"), 0, 100, default=0.0)
        }

    def _clean_disk(self, disk):
        return {
            "total_disk": disk.get("total_disk") or 0,
            "used_disk": disk.get("used_disk") or 0,
            "free_disk": disk.get("free_disk") or 0,
            "disk_percent": self._clamp(disk.get("disk_percent"), 0, 100, default=0.0)
        }

    def _clean_network(self, network):
        return {
            "bytes_sent": max(network.get("bytes_sent") or 0, 0),
            "bytes_received": max(network.get("bytes_received") or 0, 0),
            "packets_sent": max(network.get("packets_sent") or 0, 0),
            "packets_received": max(network.get("packets_received") or 0, 0)
        }

    def _clean_processes(self, processes):
        top = processes.get("top_processes") or []
        cleaned_list = []

        for proc in top:
            if not proc.get("name"):
                continue

            cleaned_list.append({
                "pid": proc.get("pid"),
                "name": proc.get("name"),
                "cpu": self._clamp(proc.get("cpu"), 0, 100, default=0.0),
                "memory": self._clamp(proc.get("memory"), 0, 100, default=0.0)
            })

        return {"top_processes": cleaned_list}

    def _clamp(self, value, low, high, default=0.0):
        if value is None:
            return default
        try:
            value = float(value)
        except (TypeError, ValueError):
            return default
        return max(low, min(high, value))
