"""Feature extraction and dataset building for verified root-cause incidents."""

import json
from typing import Any

import numpy as np

try:
    from backend.database.incident_repository import verified_incidents
except ImportError:
    from database.incident_repository import verified_incidents


FEATURE_NAMES = [
    "cpu_percent", "memory_percent", "disk_percent", "network_total_bytes",
    "process_count", "top_process_cpu", "top_process_memory", "windows_event_count",
    "anomaly_score", "matched_rule_count", "high_cpu_usage", "high_memory_usage",
    "low_disk_space", "high_network_traffic", "runaway_process", "system_error_logged",
]


def extract_features(event_data: dict[str, Any], anomaly_info: dict[str, Any] | None, matched_rules: list[dict]) -> list[float]:
    cpu = event_data.get("cpu", {})
    memory = event_data.get("memory", {})
    disk = event_data.get("disk", {})
    network = event_data.get("network", {})
    processes = event_data.get("processes", {}).get("top_processes", [])
    windows_events = event_data.get("windows_events", [])

    top_cpu = max((float(p.get("cpu") or 0.0) for p in processes), default=0.0)
    top_memory = max((float(p.get("memory") or 0.0) for p in processes), default=0.0)
    fired = {rule.get("symptom") for rule in matched_rules}

    return [
        float(cpu.get("cpu_percent") or 0.0),
        float(memory.get("memory_percent") or 0.0),
        float(disk.get("disk_percent") or 0.0),
        float(network.get("bytes_sent") or 0.0) + float(network.get("bytes_received") or 0.0),
        float(len(processes)), top_cpu, top_memory, float(len(windows_events)),
        float((anomaly_info or {}).get("score") or 0.0), float(len(matched_rules)),
        *[1.0 if symptom in fired else 0.0 for symptom in FEATURE_NAMES[10:]],
    ]


def build_verified_dataset(db) -> tuple[np.ndarray, np.ndarray]:
    rows = verified_incidents(db)
    features, labels = [], []
    for incident, feedback in rows:
        event_data = json.loads(incident.event_data)
        anomaly_info = json.loads(incident.anomaly_info)
        matched_rules = json.loads(incident.matched_rules)
        features.append(extract_features(event_data, anomaly_info, matched_rules))
        labels.append(feedback.verified_root_cause)

    return np.asarray(features, dtype=np.float32), np.asarray(labels, dtype=object)
