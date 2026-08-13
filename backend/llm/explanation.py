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

    def explain(self, user_message: str, diagnosis: dict = None, history: list = None, ml_analysis: dict = None, metrics: dict = None) -> str:
        """
        General chat explanation used by /api/chat routes.
        Answers user questions conversationally based on real system state and chat history.
        """
        diagnosis = diagnosis or {}
        history = history or []
        ml_analysis = ml_analysis or {}
        metrics = metrics or {}

        # Extract real metrics (filtering protected system processes)
        cpu = metrics.get("cpu", {})
        cpu_pct = cpu.get("cpu_percent", 0.0)
        memory = metrics.get("memory", {})
        mem_pct = memory.get("memory_percent", 0.0)
        disk = metrics.get("disk", {})
        disk_pct = disk.get("disk_percent", 0.0)
        disk_breakdown = disk.get("breakdown") or []
        storage_summary = ""
        if disk_breakdown:
            top_folders = [f"{f.get('name')} ({f.get('size_formatted')})" for f in disk_breakdown[:3]]
            storage_summary = f" (Top Space Consumers: {', '.join(top_folders)})"

        from remediation.actions import RemediationActions
        top_procs = metrics.get("processes", {}).get("top_processes", [])
        user_procs = [p for p in top_procs if not RemediationActions.is_protected_process(p.get("name"))]
        top_p = user_procs[0] if user_procs else (top_procs[0] if top_procs else {})
        top_p_name = top_p.get("name", "Active apps")
        top_p_cpu = top_p.get("cpu", 0.0)
        top_p_mem = top_p.get("memory", 0.0)

        root_cause = diagnosis.get("root_cause")
        evidence = diagnosis.get("evidence") or []
        path = diagnosis.get("path") or []

        remediation_info = "No remediation needed (system is operating within healthy parameters)."
        if root_cause:
            clean_cause = str(root_cause).replace("_", " ")
            clean_evidence = ", ".join(str(e).replace("_", " ") for e in evidence) if evidence else "high resource load"
            path_str = " -> ".join(str(p).replace("_", " ") for p in path) if path else clean_cause
            diagnosis_info = f"Diagnosed Issue: {clean_cause} | Graph Traversal Chain: {path_str} | Symptoms: {clean_evidence}"
            try:
                from remediation.executor import REMEDIATION_POLICY, ACTION_DESCRIPTIONS
                actions = REMEDIATION_POLICY.get(root_cause, [])
                if actions:
                    primary_action = actions[0].replace('_', ' ')
                    desc = ACTION_DESCRIPTIONS.get(actions[0], '')
                    remediation_info = f"Recommended Fix: {primary_action} ({desc}). Instruct user to approve in the Fix & Approval tab."
            except Exception:
                remediation_info = "Automated optimization available in Fix & Approval tab."
        else:
            diagnosis_info = "System health status: healthy, normal operations."

        context_prompt = (
            f"SYSTEM METRICS:\n"
            f"- CPU Usage: {cpu_pct}%\n"
            f"- RAM Usage: {mem_pct}%\n"
            f"- Disk Usage: {disk_pct}%{storage_summary}\n"
            f"- Active App: {top_p_name} ({top_p_cpu}% CPU, {top_p_mem}% RAM)\n"
            f"- Reasoning Engine Diagnosis: {diagnosis_info}\n"
            f"- Remediation Capability: {remediation_info}\n\n"
            f"USER QUERY: {user_message}\n\n"
            f"INSTRUCTION: Answer the USER QUERY in 1 to 3 clear, short, exact sentences using the Reasoning Engine facts above. If recommending a fix, tell user to approve it in the Fix & Approval tab."
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        # Add rolling chat history so context is preserved across turns
        for turn in history[-10:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": context_prompt})

        return self.provider.chat(messages, max_tokens=100)

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
