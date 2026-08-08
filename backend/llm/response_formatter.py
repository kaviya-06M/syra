"""
SYRA Response Formatter
========================
Post-processes the raw LLM text into structured output that the
Electron frontend and notification system can consume.
"""

import re
import json


class ResponseFormatter:
    """
    Takes raw Llama output and produces a clean dict with:
      - message:        the user-facing text
      - action_required: whether the user needs to approve something
      - severity:        for UI styling (info / warning / critical / success)
      - sections:        parsed breakdown (explanation, reasoning, recommendation)
    """

    def format_diagnosis(self, llm_text: str, diagnosis: dict) -> dict:
        """Formats the post-diagnosis explanation for the UI."""
        severity = self._severity_from_confidence(diagnosis.get("confidence", 0))

        return {
            "type": "diagnosis",
            "message": llm_text.strip(),
            "severity": severity,
            "action_required": True,
            "root_cause": diagnosis.get("root_cause"),
            "confidence": diagnosis.get("confidence"),
            "sections": self._parse_sections(llm_text),
        }

    def format_proposal(self, llm_text: str, action_name: str) -> dict:
        """Formats the remediation proposal for the permission prompt."""
        return {
            "type": "proposal",
            "message": llm_text.strip(),
            "severity": "warning",
            "action_required": True,
            "proposed_action": action_name,
        }

    def format_remediation_result(self, llm_text: str, verification: dict) -> dict:
        """Formats the post-remediation report."""
        resolved = verification.get("resolved", False)

        return {
            "type": "remediation_result",
            "message": llm_text.strip(),
            "severity": "success" if resolved else "warning",
            "action_required": not resolved,
            "resolved": resolved,
        }

    def format_chat(self, llm_text: str) -> dict:
        """Formats a general chat response."""
        return {
            "type": "chat",
            "message": llm_text.strip(),
            "severity": "info",
            "action_required": False,
        }

    def format_welcome(self, llm_text: str, health_status: str) -> dict:
        """Formats the welcome/greeting message."""
        return {
            "type": "welcome",
            "message": llm_text.strip(),
            "severity": "info" if health_status == "healthy" else "warning",
            "action_required": False,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _severity_from_confidence(self, confidence: float) -> str:
        if confidence >= 0.8:
            return "critical"
        elif confidence >= 0.5:
            return "warning"
        return "info"

    def _parse_sections(self, text: str) -> dict:
        """
        Attempts to extract numbered sections from the LLM response.
        Falls back to the full text if no structure is detected.
        """
        sections = {}

        # Try to match "1. ...", "2. ...", "3. ..."
        pattern = r"(\d)\.\s*(.+?)(?=\n\d\.\s|\Z)"
        matches = re.findall(pattern, text, re.DOTALL)

        labels = {
            "1": "explanation",
            "2": "reasoning",
            "3": "recommendation",
        }

        for num, content in matches:
            key = labels.get(num, f"section_{num}")
            sections[key] = content.strip()

        if not sections:
            sections["explanation"] = text.strip()

        return sections

    def to_json(self, formatted: dict) -> str:
        """Serialises a formatted response for the Electron IPC bridge."""
        return json.dumps(formatted, indent=2, ensure_ascii=False)
