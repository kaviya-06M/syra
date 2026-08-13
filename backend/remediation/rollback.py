













 




import os
import shutil
import subprocess

import psutil


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
            "lower_process_priority": self._rollback_process_priority,
			"close_browser_tab": self._rollback_browser_tab,
            "clear_temp_files": self._rollback_temp_cleanup,
            "flush_dns": self._rollback_irreversible,
            "free_memory": self._rollback_irreversible,
        }

    def rollback(self, action_result):
        action_name = action_result.get("action")
        handler = self._handlers.get(action_name, self._rollback_noop)
        return handler(action_result)

    def _rollback_restart_service(self, action_result):
        service = action_result.get("target", {}).get("service_name")
        if not service:
            return {"success": False, "message": "No service info available to roll back"}

        was_running = action_result.get("rollback_data", {}).get("was_running")
        if was_running is False:
            result = subprocess.run(["net", "stop", service], check=False, capture_output=True, text=True)
            return {"success": result.returncode == 0, "message": f"Restored '{service}' to its previous stopped state"}
        return {"success": True, "message": f"'{service}' was running before remediation; no service state change to undo"}

    def _rollback_kill_process(self, action_result):
        return {
            "success": False,
            "message": "Terminated processes cannot be automatically restarted. "
                        "Please relaunch the application manually if needed."
        }

    def _rollback_process_priority(self, action_result):
        target = action_result.get("target", {})
        previous_priority = action_result.get("previous_priority")
        if not target.get("pid") or previous_priority is None:
            return {"success": False, "message": "No previous process priority was recorded"}
        try:
            process = psutil.Process(target["pid"])
            if process.name().casefold() != str(target.get("name", "")).casefold():
                return {"success": False, "message": "Process PID no longer matches the remediated target"}
            process.nice(previous_priority)
            return {"success": True, "message": f"Restored priority for {target.get('name')} (pid {target.get('pid')})"}
        except Exception as exc:
            return {"success": False, "message": f"Could not restore process priority: {exc}"}

    def _rollback_browser_tab(self, action_result):
        return {
            "success": False,
            "message": "A browser tab closed with Ctrl+W cannot be reopened automatically.",
        }

    def _rollback_temp_cleanup(self, action_result):
        items = action_result.get("rollback_data", {}).get("quarantined_items", [])
        restored, skipped = 0, []
        for item in items:
            source, destination = item.get("quarantined"), item.get("original")
            try:
                if not source or not destination or not os.path.exists(source) or os.path.exists(destination):
                    skipped.append(destination)
                    continue
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                shutil.move(source, destination)
                restored += 1
            except Exception:
                skipped.append(destination)
        return {
            "success": not skipped,
            "message": f"Restored {restored} quarantined temp items",
            "restored": restored,
            "skipped": skipped,
        }

    def _rollback_irreversible(self, action_result):
        return {
            "success": False,
            "message": f"'{action_result.get('action')}' changes live operating-system state and cannot be restored automatically.",
        }

    def _rollback_noop(self, action_result):
        return {
            "success": True,
            "message": f"No rollback needed for action '{action_result.get('action')}'"
        }
