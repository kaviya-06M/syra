class PermissionManager:
    """
    Implements the 'Ask for permission' -> Yes/No branch of the SYRA
    flowchart. SYRA never runs a remediation action without the user
    explicitly approving it first.
    """

    def __init__(self):
        self._pending = {}

    def request_permission(self, action_id, action_name, root_cause, description):
        """
        Registers a pending action awaiting user approval and returns the
        prompt that should be shown/spoken to the user (e.g. after SYRA
        says 'Can you fix it?' -> user says 'Yes'/'No').
        """
        self._pending[action_id] = {
            "action_name": action_name,
            "root_cause": root_cause,
            "description": description,
            "status": "pending"
        }

        return {
            "action_id": action_id,
            "prompt": (
                f"I found the likely cause: {root_cause}. "
                f"I can fix this by running '{action_name}'. "
                f"{description} Do you want me to proceed?"
            )
        }

    def respond(self, action_id, approved):
        """Records the user's Yes/No answer for a pending action."""
        if action_id not in self._pending:
            return {"success": False, "message": "Unknown action_id"}

        self._pending[action_id]["status"] = "approved" if approved else "denied"
        return {"success": True, "status": self._pending[action_id]["status"]}

    def is_approved(self, action_id):
        return self._pending.get(action_id, {}).get("status") == "approved"

    def is_denied(self, action_id):
        return self._pending.get(action_id, {}).get("status") == "denied"

    def clear(self, action_id):
        self._pending.pop(action_id, None)
