from datetime import datetime
import re

from .actions import RemediationActions
from .permissions import PermissionManager


# Ordered from lower-risk interventions to more disruptive ones. The first
# feasible action is proposed by default; the user can select any listed
# alternative before granting approval.
REMEDIATION_POLICY = {
    "cpu_bottleneck": ["lower_process_priority", "close_browser_tab", "kill_top_process"],
    "runaway_process": ["lower_process_priority", "close_browser_tab", "kill_top_process"],
    "memory_leak": ["free_memory", "close_browser_tab", "lower_process_priority", "kill_top_process"],
    "excessive_swapping": ["free_memory", "lower_process_priority"],
    "disk_io_bottleneck": ["clear_temp_files"],
    "low_disk_space": ["clear_temp_files"],
    "network_congestion": ["flush_dns"],
    "driver_or_service_failure": ["restart_service"],
    "system_slowdown": ["lower_process_priority", "close_browser_tab", "free_memory", "clear_temp_files", "kill_top_process"],
}

# Backward-compatible default action lookup. New code should use
# REMEDIATION_POLICY so it can present multiple choices.
ACTION_MAP = {cause: actions[0] for cause, actions in REMEDIATION_POLICY.items()}

ACTION_DESCRIPTIONS = {
	"close_browser_tab": "This will focus the approved browser window and send Ctrl+W to close one active browser tab. It will not terminate the browser.",
    "kill_top_process": "This will close the process using the most resources.",
    "lower_process_priority": "This will lower the selected process priority before closing it.",
    "clear_temp_files": "This will quarantine temporary files to free disk space; they can be restored if verification fails.",
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

    def propose_action(self, action_id, root_cause, snapshot, incident_id=None, service_name=None, selected_action=None):
        """Resolves the fix for a root cause and asks the user for
        permission to run it."""
        policy_actions = REMEDIATION_POLICY.get(root_cause)
        if not policy_actions:
            return {
                "success": False,
                "message": f"No known remediation for root cause '{root_cause}'"
            }

        if selected_action is not None and selected_action not in policy_actions:
            return {"success": False, "message": "Selected action is not allowed for this root cause"}

        candidates = []
        for candidate_action in policy_actions:
            candidate_target = self._resolve_target(candidate_action, snapshot, service_name)
            if candidate_target is not None:
                candidates.append({
                    "action": candidate_action,
                    "description": ACTION_DESCRIPTIONS.get(candidate_action, "This will attempt to resolve the detected issue."),
                    "target": candidate_target,
                })

        if not candidates:
            return {"success": False, "message": "No safe remediation target is available"}

        proposal = next((item for item in candidates if item["action"] == selected_action), candidates[0])
        action_name = proposal["action"]

        description = proposal["description"]
        target = proposal["target"]

        response = self.permissions.request_permission(
            action_id=action_id,
            action_name=action_name,
            root_cause=root_cause,
            description=description,
            target=target,
            incident_id=incident_id,
        )
        # The UI needs these details to show a transparent approval request.
        response["root_cause"] = root_cause
        response["description"] = description
        response["alternatives"] = candidates
        return response

    def execute(self, action_id):
        """Execute only the action and target that the user approved."""
        approved = self.permissions.get_approved(action_id)
        if approved is None:
            return {"success": False, "message": "Action not approved by user"}

        action_name = approved["action_name"]
        method = getattr(self.actions, action_name, None)

        if not method:
            return {"success": False, "message": f"Unknown action '{action_name}'"}

        target = approved["target"]
        kwargs = dict(target.get("kwargs", {}))
        if action_name == "clear_temp_files":
            # The cleanup action uses this stable ID to place files in a
            # recoverable quarantine rather than deleting them immediately.
            kwargs["rollback_id"] = action_id
        result = method(**kwargs)
        result["timestamp"] = datetime.now().isoformat()
        result["action_id"] = action_id
        result["root_cause"] = approved["root_cause"]
        result["incident_id"] = approved.get("incident_id")
        result["approved_target"] = target

        self.history.append(result)
        self.permissions.clear(action_id)

        return result

    def get_last_action(self):
        return self.history[-1] if self.history else None

    def get_action(self, action_id):
        return next((item for item in reversed(self.history) if item.get("action_id") == action_id), None)

    def _resolve_target(self, action_name, snapshot, service_name):
        snapshot = snapshot or {}
        if action_name == "close_browser_tab":
            processes = snapshot.get("processes", {}).get("top_processes", [])
            candidates = [
                process for process in processes
                if process.get("pid") and self.actions.is_browser_process(process.get("name"))
            ]
            if not candidates:
                return None
            process = max(candidates, key=lambda item: float(item.get("memory") or item.get("cpu") or 0.0))
            return {
                "kind": "browser_tab",
                "display_name": f"one tab in {process.get('name')} (PID {process.get('pid')})",
                "kwargs": {"pid": int(process["pid"]), "expected_name": process.get("name")},
            }

        if action_name in {"kill_top_process", "lower_process_priority"}:
            processes = snapshot.get("processes", {}).get("top_processes", [])
            candidates = [
                process for process in processes
                if process.get("pid") and not self.actions.is_protected_process(process.get("name"))
            ]
            if not candidates:
                return None
            process = max(candidates, key=lambda item: float(item.get("cpu") or 0.0))
            return {
                "kind": "process",
                "display_name": f"process {process.get('name')} (PID {process.get('pid')})",
                "kwargs": {"pid": int(process["pid"]), "expected_name": process.get("name")},
            }

        if action_name == "restart_service":
            if not service_name or not re.fullmatch(r"[A-Za-z0-9_.-]+", service_name):
                return None
            return {
                "kind": "service",
                "display_name": f"Windows service {service_name}",
                "kwargs": {"service_name": service_name},
            }

        fixed_targets = {
            "clear_temp_files": ("user temporary-files directory", {}),
            "flush_dns": ("Windows DNS resolver cache", {}),
            "free_memory": ("background-process working sets", {}),
        }
        display_name, kwargs = fixed_targets.get(action_name, (None, None))
        if display_name is None:
            return None
        return {"kind": "system_scope", "display_name": display_name, "kwargs": kwargs}
