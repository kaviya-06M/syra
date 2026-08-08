"""
notifications package
Desktop alerting for SIRA: fires a toast (and optionally speaks) when the
diagnosis pipeline finds a high-confidence, non-repeating anomaly.

Usage:
    from notifications import NotificationService, ToastNotifier, get_default_notification_service

    notifier = get_default_notification_service()
    notifier.notify_diagnosis(diagnosis, explanation, speak=True)
"""

from notifications.notification_service import (
    NotificationService,
    get_default_notification_service,
)
from notifications.toast import ToastNotifier

__all__ = [
    "NotificationService",
    "ToastNotifier",
    "get_default_notification_service",
]
