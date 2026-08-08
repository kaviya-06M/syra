from typing import Dict, List


class FeatureEngineer:
    """
    Converts a cleaned SYRA system event into a fixed-length
    numerical feature vector for the LSTM Autoencoder.
    """

    FEATURE_NAMES = [
        "cpu_percent",
        "memory_percent",
        "disk_percent",
        "network_bytes_sent",
        "network_bytes_received",
        "network_packets_sent",
        "network_packets_received",
        "process_count",
        "top_process_cpu",
        "top_process_memory",
        "windows_event_count",
    ]

    def transform(self, event: Dict) -> List[float]:

        cpu = event.get("cpu", {})
        memory = event.get("memory", {})
        disk = event.get("disk", {})
        network = event.get("network", {})
        processes = event.get("processes", {})
        windows_events = event.get("windows_events", [])

        cpu_percent = self._safe_float(
            cpu.get("cpu_percent")
        )

        memory_percent = self._safe_float(
            memory.get("memory_percent")
        )

        disk_percent = self._safe_float(
            disk.get("disk_percent")
        )

        bytes_sent = self._safe_float(
            network.get("bytes_sent")
        )

        bytes_received = self._safe_float(
            network.get("bytes_received")
        )

        packets_sent = self._safe_float(
            network.get("packets_sent")
        )

        packets_received = self._safe_float(
            network.get("packets_received")
        )

        top_processes = processes.get(
            "top_processes",
            []
        )

        process_count = len(top_processes)

        top_process_cpu = 0.0
        top_process_memory = 0.0

        if top_processes:

            top_cpu_process = max(
                top_processes,
                key=lambda process: self._safe_float(
                    process.get("cpu")
                )
            )

            top_memory_process = max(
                top_processes,
                key=lambda process: self._safe_float(
                    process.get("memory")
                )
            )

            top_process_cpu = self._safe_float(
                top_cpu_process.get("cpu")
            )

            top_process_memory = self._safe_float(
                top_memory_process.get("memory")
            )

        windows_event_count = len(
            windows_events
        )

        return [
            cpu_percent,
            memory_percent,
            disk_percent,
            bytes_sent,
            bytes_received,
            packets_sent,
            packets_received,
            float(process_count),
            top_process_cpu,
            top_process_memory,
            float(windows_event_count),
        ]

    @staticmethod
    def _safe_float(
        value,
        default: float = 0.0
    ) -> float:

        try:
            if value is None:
                return default

            return float(value)

        except (TypeError, ValueError):
            return default

    @classmethod
    def feature_names(cls) -> List[str]:
        return cls.FEATURE_NAMES.copy()

    @classmethod
    def feature_count(cls) -> int:
        return len(cls.FEATURE_NAMES)