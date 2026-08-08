"""
SYRA Conversation Memory
=========================
Maintains a rolling window of chat messages so Llama 3.1 has context
when the user asks follow-up questions like "Can you fix it?" or
"What caused it?".
"""

from collections import deque
from datetime import datetime


class ConversationMemory:
    """
    Stores the chat history between the user and SYRA. The system prompt
    is always prepended, and the window is capped to stay within the
    model's context budget.
    """

    def __init__(self, max_turns: int = 20, system_prompt: str = ""):
        self.max_turns = max_turns
        self.system_prompt = system_prompt
        self._history = deque(maxlen=max_turns * 2)  # user + assistant = 2 msgs per turn
        self._diagnosis_context = None
        self._remediation_context = None

    # ── Message management ────────────────────────────────────────────────────

    def add_user_message(self, content: str):
        self._history.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def add_assistant_message(self, content: str):
        self._history.append({
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def add_system_event(self, content: str):
        """Injects a system-level context message (e.g. new anomaly detected)."""
        self._history.append({
            "role": "user",
            "content": f"[SYSTEM EVENT] {content}",
            "timestamp": datetime.now().isoformat(),
        })

    # ── Context injection ─────────────────────────────────────────────────────

    def set_diagnosis_context(self, diagnosis: dict):
        """Stores the latest RootCauseEngine diagnosis for follow-up questions."""
        self._diagnosis_context = diagnosis

    def set_remediation_context(self, remediation: dict):
        """Stores the latest remediation result for follow-up questions."""
        self._remediation_context = remediation

    # ── Build messages for LLM ────────────────────────────────────────────────

    def get_messages(self) -> list:
        """
        Returns the full message list ready for LLMProvider.chat():
          [system_prompt, ...context..., ...history...]
        """
        messages = []

        # 1. System prompt
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        # 2. Inject active diagnosis/remediation context
        context_parts = []
        if self._diagnosis_context:
            ctx = self._diagnosis_context
            context_parts.append(
                f"Active diagnosis: root_cause={ctx.get('root_cause')}, "
                f"confidence={ctx.get('confidence')}, "
                f"evidence={ctx.get('evidence')}"
            )
        if self._remediation_context:
            ctx = self._remediation_context
            context_parts.append(
                f"Last remediation: action={ctx.get('action')}, "
                f"success={ctx.get('success')}, "
                f"message={ctx.get('message')}"
            )

        if context_parts:
            messages.append({
                "role": "system",
                "content": "Current SYRA context:\n" + "\n".join(context_parts),
            })

        # 3. Conversation history
        for msg in self._history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        return messages

    # ── Utilities ─────────────────────────────────────────────────────────────

    def clear(self):
        self._history.clear()
        self._diagnosis_context = None
        self._remediation_context = None

    @property
    def turn_count(self) -> int:
        return len([m for m in self._history if m["role"] == "user"])

    @property
    def last_user_message(self) -> str:
        for msg in reversed(self._history):
            if msg["role"] == "user":
                return msg["content"]
        return ""
