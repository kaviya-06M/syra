"""
SYRA Chat Engine (memory.py)
=============================
The main chat interface that ties together:
  - LLMProvider (NVIDIA NIM)
  - ConversationMemory (rolling history)
  - ExplanationEngine (structured → language)
  - ResponseFormatter (language → UI-ready dict)

This is what the FastAPI chat route and the Electron frontend call.
"""

from .provider import LLMProvider
from .conversation_memory import ConversationMemory
from .explanation import ExplanationEngine
from .response_formatter import ResponseFormatter
from .prompts import SYSTEM_PROMPT, CHAT_TEMPLATE, WELCOME_TEMPLATE


class SyraChatEngine:
    """
    Unified chat interface for the SYRA application.

    Usage from FastAPI:
        engine = SyraChatEngine()
        response = engine.chat("What's wrong with my computer?", system_state={...})
    """

    def __init__(self, provider: LLMProvider = None):
        self.provider = provider or LLMProvider()
        self.memory = ConversationMemory(
            max_turns=20,
            system_prompt=SYSTEM_PROMPT,
        )
        self.explanation = ExplanationEngine(provider=self.provider)
        self.formatter = ResponseFormatter()

    # ── General chat ──────────────────────────────────────────────────────────

    def chat(self, user_message: str, system_state: dict = None) -> dict:
        """
        Handles a user message in the chat window.

        Parameters
        ----------
        user_message : str
            What the user typed or spoke.
        system_state : dict, optional
            Current system snapshot with cpu, memory, disk, processes.
        """
        system_state = system_state or {}
        self.memory.add_user_message(user_message)

        # Build the context-enriched user prompt
        top_proc = self._get_top_process(system_state)
        recent_diag = self._format_recent_diagnosis()

        enriched_prompt = CHAT_TEMPLATE.format(
            cpu_percent=system_state.get("cpu", {}).get("cpu_percent", "?"),
            memory_percent=system_state.get("memory", {}).get("memory_percent", "?"),
            disk_percent=system_state.get("disk", {}).get("disk_percent", "?"),
            top_process=top_proc.get("name", "N/A"),
            top_process_cpu=top_proc.get("cpu", "?"),
            top_process_mem=top_proc.get("memory", "?"),
            recent_diagnosis=recent_diag,
            user_message=user_message,
        )

        # Use conversation history + enriched prompt
        messages = self.memory.get_messages()
        # Replace the last user message with the enriched version
        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] = enriched_prompt

        response_text = self.provider.chat(messages)
        self.memory.add_assistant_message(response_text)

        return self.formatter.format_chat(response_text)

    # ── Diagnosis explanation (called by pipeline, not by user) ───────────────

    def explain_diagnosis(self, diagnosis: dict, anomaly_report: dict = None) -> dict:
        """
        Called when RootCauseEngine produces a diagnosis.
        Generates explanation and stores context for follow-up chat.
        """
        self.memory.set_diagnosis_context(diagnosis)

        llm_text = self.explanation.explain_diagnosis(diagnosis, anomaly_report)
        self.memory.add_assistant_message(llm_text)

        return self.formatter.format_diagnosis(llm_text, diagnosis)

    # ── Remediation proposal ──────────────────────────────────────────────────

    def explain_proposal(self, root_cause: str, action_name: str,
                         action_description: str, risk_level: str = "low") -> dict:
        """
        Called before PermissionManager asks the user Yes/No.
        Generates the 'Can I fix this?' message.
        """
        llm_text = self.explanation.explain_proposal(
            root_cause, action_name, action_description, risk_level
        )
        self.memory.add_assistant_message(llm_text)

        return self.formatter.format_proposal(llm_text, action_name)

    # ── Post-remediation report ───────────────────────────────────────────────

    def explain_remediation(self, action_result: dict, verification: dict,
                            before_snapshot: dict, after_snapshot: dict) -> dict:
        """
        Called after Verifier checks whether the fix worked.
        Generates the final 'resolved' or 'issue persists' message.
        """
        self.memory.set_remediation_context(action_result)

        llm_text = self.explanation.explain_remediation(
            action_result, verification, before_snapshot, after_snapshot
        )
        self.memory.add_assistant_message(llm_text)

        return self.formatter.format_remediation_result(llm_text, verification)

    # ── Welcome message ───────────────────────────────────────────────────────

    def welcome(self, system_state: dict = None) -> dict:
        """Generates the greeting when the user opens SYRA."""
        system_state = system_state or {}

        cpu = system_state.get("cpu", {}).get("cpu_percent", 0)
        mem = system_state.get("memory", {}).get("memory_percent", 0)
        disk = system_state.get("disk", {}).get("disk_percent", 0)

        health = "healthy"
        if cpu >= 85 or mem >= 85 or disk >= 90:
            health = "issues detected"

        prompt = WELCOME_TEMPLATE.format(
            cpu_percent=cpu,
            memory_percent=mem,
            disk_percent=disk,
            health_status=health,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        llm_text = self.provider.chat(messages)
        self.memory.add_assistant_message(llm_text)

        return self.formatter.format_welcome(llm_text, health)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_top_process(self, state: dict) -> dict:
        procs = state.get("processes", {}).get("top_processes", [])
        if procs:
            return procs[0]
        return {"name": "N/A", "cpu": 0, "memory": 0}

    def _format_recent_diagnosis(self) -> str:
        ctx = self.memory._diagnosis_context
        if not ctx:
            return "No recent diagnosis."
        return (
            f"Root cause: {ctx.get('root_cause', 'unknown')}, "
            f"Confidence: {ctx.get('confidence', 0)}, "
            f"Evidence: {ctx.get('evidence', [])}"
        )

    def clear_memory(self):
        self.memory.clear()
