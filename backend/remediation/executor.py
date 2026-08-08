from datetime import datetime

from .actions import RemediationActions
from .permissions import PermissionManager


# Maps a root cause (as produced by reasoning.RootCauseEngine) to the
# remediation action that should fix it.
ACTION_MAP = {
    "cpu_bottleneck": "kill_top_process",
    "runaway_process": "kill_top_process",
    "memory_leak": "kill_top_process",
    "excessive_swapping": "free_memory",
    "disk_io_bottleneck": "clear_temp_files",
    "low_disk_space": "clear_temp_files",
    "network_congestion": "flush_dns",
    "driver_or_service_failure": "restart_service",
    "system_slowdown": "kill_top_process",
}

ACTION_DESCRIPTIONS = {
    "kill_top_process": "This will close the process using the most resources.",
    "clear_temp_files": "This will delete temporary files to free up disk space.",
    "flush_dns": "This will reset your network's DNS cache.",
    "restart_service": "This will restart the affected background service.",
    "free_memory": "This will trim memory usage of background processes.",
}


class RemediationExecutor:
    """
    Implements the 'Execute Action' step of the SYRA pipeline. Given a
    root cause diagnosis, resolves the correct remediation action, but
    only actually runs it once PermissionManager confirms the user said
    Yes to 'Can you fix it?'.
    """

    def __init__(self):
        self.actions = RemediationActions()
        self.permissions = PermissionManager()
        self.history = []

    def propose_action(self, action_id, root_cause):
        """Resolves the fix for a root cause and asks the user for
        permission to run it."""
        action_name = ACTION_MAP.get(root_cause)

        if not action_name:
            return {
                "success": False,
                "message": f"No known remediation for root cause '{root_cause}'"
            }

        description = ACTION_DESCRIPTIONS.get(
            action_name, "This will attempt to resolve the detected issue."
        )

        return self.permissions.request_permission(
            action_id=action_id,
            action_name=action_name,
            root_cause=root_cause,
            description=description
        )

    def execute(self, action_id, root_cause, **kwargs):
        """Runs the mapped action for the given root cause, but only if
        the user has approved it via PermissionManager."""
        if not self.permissions.is_approved(action_id):
            return {"success": False, "message": "Action not approved by user"}

        action_name = ACTION_MAP.get(root_cause)
        method = getattr(self.actions, action_name, None)

        if not method:
            return {"success": False, "message": f"Unknown action '{action_name}'"}

        result = method(**kwargs)
        result["timestamp"] = datetime.now().isoformat()
        result["action_id"] = action_id
        result["root_cause"] = root_cause

        self.history.append(result)
        self.permissions.clear(action_id)

        return result

    def get_last_action(self):
        return self.history[-1] if self.history else None
