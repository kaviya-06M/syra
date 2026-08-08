"""
notification_service.py
Decides WHEN and HOW to alert the user, then dispatches to the actual
toast popup (and optionally speaks it). Sits between the orchestrator's
diagnosis output and the user's desktop -- so the LSTM/knowledge-graph
pipeline can run every few seconds without spamming a toast every time.

Responsibilities:
- De-dupe: don't re-alert on the same root cause repeatedly while it's ongoing
- Cooldown: enforce a minimum gap between notifications overall
- Severity gating: only notify above a confidence threshold
- Optional voice: speak the explanation aloud when the user has voice enabled
"""

import time

from config import settings
from notifications.toast import ToastNotifier


class NotificationService:
    def __init__(
        self,
        toast: ToastNotifier | None = None,
        voice=None,
        cooldown_seconds: int = 300,
        min_confidence: int = 60,
        repeat_suppress_seconds: int = 900,
    ):
        """
        toast: ToastNotifier instance (created if not supplied)
        voice: optional VoiceInterface (from voice.py) to speak alerts aloud
        cooldown_seconds: minimum gap between ANY two notifications
        min_confidence: skip notifying if diagnosis confidence is below this
        repeat_suppress_seconds: don't re-alert on the SAME root cause within this window
        """
        self.toast = toast or ToastNotifier()
        self.voice = voice
        self.cooldown_seconds = cooldown_seconds
        self.min_confidence = min_confidence
        self.repeat_suppress_seconds = repeat_suppress_seconds

        self._last_notified_at: float = 0.0
        self._last_root_cause: str | None = None
        self._last_root_cause_at: float = 0.0

    # -------- gating logic --------

    def _in_global_cooldown(self, now: float) -> bool:
        return (now - self._last_notified_at) < self.cooldown_seconds

    def _is_repeat_root_cause(self, root_cause: str, now: float) -> bool:
        return (
            root_cause == self._last_root_cause
            and (now - self._last_root_cause_at) < self.repeat_suppress_seconds
        )

    def _should_notify(self, diagnosis: dict) -> bool:
        now = time.monotonic()

        if diagnosis.get("confidence", 0) < self.min_confidence:
            return False
        if self._in_global_cooldown(now):
            return False
        if self._is_repeat_root_cause(diagnosis.get("root_cause", ""), now):
            return False
        return True

    def _record_notification(self, root_cause: str):
        now = time.monotonic()
        self._last_notified_at = now
        self._last_root_cause = root_cause
        self._last_root_cause_at = now

    # -------- public API --------

    def notify_diagnosis(self, diagnosis: dict, explanation: str, speak: bool = False):
        """
        Called by the orchestrator after a full diagnosis pipeline run.
        `diagnosis` is the dict from DiagnosisBuilder.build().
        `explanation` is the LLM's plain-language text.
        """
        if not self._should_notify(diagnosis):
            return False

        title = f"SIRA detected: {diagnosis['problem']}"
        # Toasts should stay short; the full explanation is available via /diagnose or voice.
        body = self._truncate(explanation, 180)

        self.toast.show(title=title, message=body)

        if speak and self.voice is not None:
            self.voice.say(explanation)

        self._record_notification(diagnosis["root_cause"])
        return True

    def notify_custom(self, title: str, message: str, speak: bool = False):
        """For ad-hoc alerts outside the anomaly pipeline (e.g. agent errors, install success)."""
        self.toast.show(title=title, message=message)
        if speak and self.voice is not None:
            self.voice.say(message)

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        text = text.strip()
        return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…"


def get_default_notification_service() -> NotificationService:
    """Factory used by the orchestrator/main app to get a ready-to-use instance."""
    try:
        from voice import VoiceInterface

        voice = VoiceInterface()
    except Exception as exc:
        print(f"[NotificationService] voice unavailable, alerts will be silent: {exc}")
        voice = None

    return NotificationService(
        toast=ToastNotifier(),
        voice=voice,
        cooldown_seconds=getattr(settings, "NOTIFY_COOLDOWN_SECONDS", 300),
        min_confidence=getattr(settings, "NOTIFY_MIN_CONFIDENCE", 60),
    )
