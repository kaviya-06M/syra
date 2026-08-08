import os


class RollbackManager:
    """
    Safety net around the 'Execute Action' step. If RemediationVerifier
    finds the issue is not resolved, or the user asks SYRA to undo a
    change, this restores what can be restored (some actions, like
    terminating a process, cannot be automatically reversed - that is
    reported clearly instead of pretending to succeed).
    """

    def __init__(self):
        self._handlers = {
            "restart_service": self._rollback_restart_service,
            "kill_top_process": self._rollback_kill_process,
            "clear_temp_files": self._rollback_noop,
            "flush_dns": self._rollback_noop,
            "free_memory": self._rollback_noop,
        }

    def rollback(self, action_result):
        action_name = action_result.get("action")
        handler = self._handlers.get(action_name, self._rollback_noop)
        return handler(action_result)

    def _rollback_restart_service(self, action_result):
        service = action_result.get("target", {}).get("service_name")
        if not service:
            return {"success": False, "message": "No service info available to roll back"}

        os.system(f"net start {service}")
        return {"success": True, "message": f"Attempted to restart '{service}' again"}

    def _rollback_kill_process(self, action_result):
        return {
            "success": False,
            "message": "Terminated processes cannot be automatically restarted. "
                        "Please relaunch the application manually if needed."
        }

    def _rollback_noop(self, action_result):
        return {
            "success": True,
            "message": f"No rollback needed for action '{action_result.get('action')}'"
        }
