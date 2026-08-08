"""
SYRA Explanation Engine
========================
The bridge between the structured pipeline output and human language.

Two entry points, matching your pipeline diagram:
  1. explain_diagnosis()  — Called after RootCauseEngine
  2. explain_remediation() — Called after Verifier
"""

from .provider import LLMProvider
from .prompts import (
    SYSTEM_PROMPT,
    CHAT_TEMPLATE,
    DIAGNOSIS_TEMPLATE,
    REMEDIATION_PROPOSAL_TEMPLATE,
    POST_REMEDIATION_TEMPLATE,
)


class ExplanationEngine:
    """
    Converts structured facts from the SYRA pipeline into natural
    language using Llama 3.1 70B Instruct via NVIDIA NIM.

    The LLM does NOT diagnose. It only translates facts into language.
    """

    def __init__(self, provider: LLMProvider = None):
        self.provider = provider or LLMProvider()

    def explain(self, user_message: str, diagnosis: dict = None, history: list = None) -> str:
        """
        General chat explanation used by /api/chat routes.

        If diagnosis context exists, the response is instructed to clearly
        state the root cause in the first sentence.
        """
        diagnosis = diagnosis or {}
        history = history or []

        root_cause = diagnosis.get("root_cause")
        confidence = diagnosis.get("confidence")
        evidence = diagnosis.get("evidence") or []

        if root_cause:
            recent_diagnosis = (
                f"Root cause: {root_cause}\n"
                f"Confidence: {confidence}\n"
                f"Evidence: {evidence}"
            )
            extra_instruction = (
                "If a root cause is available, your first sentence must start with "
                "'Root cause:' and include the exact root cause text. Then add a "
                "brief second paragraph that explains why it matters and what the "
                "user should do next, using the evidence provided."
            )
        else:
            recent_diagnosis = "No recent diagnosis."
            extra_instruction = "If no diagnosis exists, say that clearly and ask to run diagnosis."

        user_content = CHAT_TEMPLATE.format(
            cpu_percent="?",
            memory_percent="?",
            disk_percent="?",
            top_process="N/A",
            top_process_cpu="?",
            top_process_mem="?",
            recent_diagnosis=recent_diagnosis,
            user_message=user_message,
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "system", "content": extra_instruction})
        messages.append({"role": "user", "content": user_content})

        return self.provider.chat(messages)

    # ── 1. After RootCauseEngine ──────────────────────────────────────────────

    def explain_diagnosis(self, diagnosis: dict, anomaly_report: dict = None) -> str:
        """
        Takes structured output from RootCauseEngine.diagnose() and the
        AnomalyDetector report and asks Llama to generate a user-facing
        explanation.

        Parameters
        ----------
        diagnosis : dict
            Output of RootCauseEngine.diagnose():
              {root_cause, confidence, evidence, path, matched_rules, ...}
        anomaly_report : dict, optional
            Output of AnomalyDetector.detect_from_events():
              {is_anomaly, anomaly_score, threshold, contributing_features, ...}
        """
        anomaly_report = anomaly_report or {}

        # Format evidence as bullet points
        evidence_list = diagnosis.get("evidence", [])
        evidence_str = "\n".join(f"  - {e}" for e in evidence_list) if evidence_list else "  - No specific evidence"

        # Format contributing metrics
        features = anomaly_report.get("contributing_features", [])
        if features:
            metrics_lines = [
                f"  - {f['feature']}: {f['contribution_percent']}% contribution"
                for f in features[:5]
            ]
            metrics_summary = "\n".join(metrics_lines)
        else:
            metrics_summary = "  - No detailed metric breakdown available"

        user_content = DIAGNOSIS_TEMPLATE.format(
            root_cause=diagnosis.get("root_cause", "unknown"),
            confidence=round((diagnosis.get("confidence", 0)) * 100, 1),
            evidence=evidence_str,
            anomaly_score=round(anomaly_report.get("anomaly_score", 0), 4),
            threshold=round(anomaly_report.get("threshold", 0), 4),
            metrics_summary=metrics_summary,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        return self.provider.chat(messages)

    # ── 2. Remediation Proposal ───────────────────────────────────────────────

    def explain_proposal(self, root_cause: str, action_name: str,
                         action_description: str, risk_level: str = "low") -> str:
        """
        Generates the 'Can I fix this?' message shown to the user before
        PermissionManager collects their Yes/No.
        """
        user_content = REMEDIATION_PROPOSAL_TEMPLATE.format(
            root_cause=root_cause,
            action_name=action_name,
            action_description=action_description,
            risk_level=risk_level,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        return self.provider.chat(messages)

    # ── 3. After Verifier ─────────────────────────────────────────────────────

    def explain_remediation(self, action_result: dict,
                            verification: dict,
                            before_snapshot: dict,
                            after_snapshot: dict) -> str:
        """
        Takes the Verifier's before/after report and generates the final
        'Issue resolved' or 'Issue persists' message.

        Parameters
        ----------
        action_result : dict
            Output of RemediationExecutor.execute()
        verification : dict
            Output of RemediationVerifier.verify()
        before_snapshot / after_snapshot : dict
            Raw event snapshots captured before and after remediation.
        """
        user_content = POST_REMEDIATION_TEMPLATE.format(
            action_name=action_result.get("action", "unknown"),
            root_cause=action_result.get("root_cause", "unknown"),
            before_cpu=before_snapshot.get("cpu", {}).get("cpu_percent", "?"),
            before_memory=before_snapshot.get("memory", {}).get("memory_percent", "?"),
            before_disk=before_snapshot.get("disk", {}).get("disk_percent", "?"),
            after_cpu=after_snapshot.get("cpu", {}).get("cpu_percent", "?"),
            after_memory=after_snapshot.get("memory", {}).get("memory_percent", "?"),
            after_disk=after_snapshot.get("disk", {}).get("disk_percent", "?"),
            resolved=verification.get("resolved", False),
            still_critical=verification.get("still_critical", False),
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        return self.provider.chat(messages)
