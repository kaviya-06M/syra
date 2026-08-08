class RuleEngine:
    """
    Rule-based evaluator that inspects the raw system metrics collected by
    the Background Agent and raises symptom flags whenever a metric crosses
    a known threshold. These symptoms feed into the CorrelationEngine,
    which builds the context graph (NetworkX) used by the Root Cause
    Reasoning Engine.
    """

    def __init__(self):
        self.rules = [
            {
                "id": "HIGH_CPU",
                "condition": lambda data: data.get("cpu", {}).get("cpu_percent", 0) >= 85,
                "symptom": "high_cpu_usage",
                "severity": "high",
                "weight": 0.8
            },
            {
                "id": "HIGH_MEMORY",
                "condition": lambda data: data.get("memory", {}).get("memory_percent", 0) >= 85,
                "symptom": "high_memory_usage",
                "severity": "high",
                "weight": 0.8
            },
            {
                "id": "LOW_DISK_SPACE",
                "condition": lambda data: data.get("disk", {}).get("disk_percent", 0) >= 90,
                "symptom": "low_disk_space",
                "severity": "medium",
                "weight": 0.6
            },
            {
                "id": "HIGH_NETWORK_TRAFFIC",
                "condition": lambda data: (
                    data.get("network", {}).get("bytes_sent", 0) +
                    data.get("network", {}).get("bytes_received", 0)
                ) > 500_000_000,
                "symptom": "high_network_traffic",
                "severity": "medium",
                "weight": 0.5
            },
            {
                "id": "RUNAWAY_PROCESS",
                "condition": lambda data: any(
                    p.get("cpu", 0) >= 50 or p.get("memory", 0) >= 30
                    for p in data.get("processes", {}).get("top_processes", [])
                ),
                "symptom": "runaway_process",
                "severity": "high",
                "weight": 0.7
            },
            {
                "id": "WINDOWS_ERROR_EVENTS",
                "condition": lambda data: len(data.get("windows_events", [])) > 0,
                "symptom": "system_error_logged",
                "severity": "low",
                "weight": 0.3
            }
        ]

    def evaluate(self, event_data):
        """
        Runs every registered rule against a single event snapshot and
        returns the list of symptoms that fired.
        """
        matched = []

        for rule in self.rules:
            try:
                if rule["condition"](event_data):
                    matched.append({
                        "rule_id": rule["id"],
                        "symptom": rule["symptom"],
                        "severity": rule["severity"],
                        "weight": rule["weight"]
                    })
            except Exception:
                continue

        return matched

    def add_rule(self, rule_id, condition, symptom, severity="medium", weight=0.5):
        """Allows new rules to be registered at runtime."""
        self.rules.append({
            "id": rule_id,
            "condition": condition,
            "symptom": symptom,
            "severity": severity,
            "weight": weight
        })
