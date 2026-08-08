"""
Fixed, non-secret values shared across SYRA's backend. Anything that
might change per-deployment (API keys, ports, URLs) belongs in
settings.py instead - this file is for values that describe SYRA's
behavior, not its environment.
"""

# --- Background Agent (Step 4: metrics collection cadence) ---
METRICS_COLLECTION_INTERVAL_SECONDS = 5
METRICS_HISTORY_LIMIT = 500

# --- reasoning.rule_engine thresholds ---
# Kept identical to the values already hardcoded in RuleEngine so both
# can be pointed at this single source of truth during the next refactor.
CPU_HIGH_THRESHOLD = 85
MEMORY_HIGH_THRESHOLD = 85
DISK_LOW_SPACE_THRESHOLD = 90
NETWORK_HIGH_TRAFFIC_BYTES = 500_000_000
PROCESS_CPU_RUNAWAY_THRESHOLD = 50
PROCESS_MEMORY_RUNAWAY_THRESHOLD = 30

# --- remediation.verifier thresholds ---
VERIFY_IMPROVEMENT_TOLERANCE = 2

# --- ml.anomaly (LSTM Autoencoder) ---
ANOMALY_SCORE_THRESHOLD = 0.7
LSTM_SEQUENCE_LENGTH = 30          # number of past snapshots per input window
LSTM_FEATURE_COUNT = 5             # cpu, memory, disk, network, process count

# --- Symptom / cause labels ---
# Central list so reasoning.knowledge_graph and reasoning.rule_engine
# never drift apart on naming.
SYMPTOMS = [
    "high_cpu_usage",
    "high_memory_usage",
    "low_disk_space",
    "high_network_traffic",
    "runaway_process",
    "system_error_logged",
]

ROOT_CAUSES = [
    "cpu_bottleneck",
    "memory_leak",
    "excessive_swapping",
    "disk_io_bottleneck",
    "network_congestion",
    "driver_or_service_failure",
    "system_slowdown",
]

# --- remediation.executor action names ---
ACTION_KILL_PROCESS = "kill_top_process"
ACTION_CLEAR_TEMP_FILES = "clear_temp_files"
ACTION_FLUSH_DNS = "flush_dns"
ACTION_RESTART_SERVICE = "restart_service"
ACTION_FREE_MEMORY = "free_memory"

# --- Confidence scoring weights (reasoning.confidence_score defaults) ---
CONFIDENCE_ANOMALY_WEIGHT = 0.4
CONFIDENCE_RULE_WEIGHT = 0.35
CONFIDENCE_REACH_WEIGHT = 0.25

# --- Notification levels ---
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
