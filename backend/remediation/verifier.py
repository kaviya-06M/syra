class RemediationVerifier:
    """
    Implements the 'Verify whether the issue is resolved' step. Compares
    system metrics captured right before and right after a remediation
    action to decide whether the fix actually worked.
    """

    def __init__(self, cpu_threshold=85, memory_threshold=85, disk_threshold=90, tolerance=2):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.tolerance = tolerance

    def verify(self, before_snapshot, after_snapshot, root_cause=None):
        before = {
            "cpu": before_snapshot.get("cpu", {}).get("cpu_percent", 0),
            "memory": before_snapshot.get("memory", {}).get("memory_percent", 0),
            "disk": before_snapshot.get("disk", {}).get("disk_percent", 0),
        }
        after = {
            "cpu": after_snapshot.get("cpu", {}).get("cpu_percent", 0),
            "memory": after_snapshot.get("memory", {}).get("memory_percent", 0),
            "disk": after_snapshot.get("disk", {}).get("disk_percent", 0),
        }
        checks = {
            "cpu_improved": self._improved(
                before_snapshot.get("cpu", {}).get("cpu_percent", 0),
                after_snapshot.get("cpu", {}).get("cpu_percent", 0)
            ),
            "memory_improved": self._improved(
                before_snapshot.get("memory", {}).get("memory_percent", 0),
                after_snapshot.get("memory", {}).get("memory_percent", 0)
            ),
            "disk_improved": self._improved(
                before_snapshot.get("disk", {}).get("disk_percent", 0),
                after_snapshot.get("disk", {}).get("disk_percent", 0)
            ),
        }

        still_critical = (
            after_snapshot.get("cpu", {}).get("cpu_percent", 0) >= self.cpu_threshold or
            after_snapshot.get("memory", {}).get("memory_percent", 0) >= self.memory_threshold or
            after_snapshot.get("disk", {}).get("disk_percent", 0) >= self.disk_threshold
        )

        resolved = any(checks.values()) and not still_critical

        return {
            "resolved": resolved,
            "still_critical": still_critical,
            "checks": checks,
            "root_cause": root_cause,
            "before": before,
            "after": after,
            "before_timestamp": before_snapshot.get("timestamp"),
            "after_timestamp": after_snapshot.get("timestamp"),
            "message": (
                "Telemetry improved after the approved action."
                if resolved else
                "The approved action completed, but the next telemetry sample does not yet show a confirmed improvement."
            ),
        }

    def _improved(self, before, after):
        return (before - after) > self.tolerance
