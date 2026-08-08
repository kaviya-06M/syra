"""
toast.py
Thin cross-platform wrapper around desktop "toast" popups.

Uses `plyer` as the primary backend (works on Windows/macOS/Linux) and, on
Windows, prefers `win10toast` when available for a more native-looking toast
with click callbacks. Never raises -- a failed toast should never crash the
agent, it just logs and moves on.
"""

import platform
import threading

try:
    from plyer import notification as _plyer_notification
except ImportError:
    _plyer_notification = None

_IS_WINDOWS = platform.system() == "Windows"

_win10toast_available = False
if _IS_WINDOWS:
    try:
        from win10toast import ToastNotifier as _Win10ToastNotifier

        _win10toast_available = True
    except ImportError:
        _win10toast_available = False


class ToastNotifier:
    """
    Fires OS-level toast popups. Safe to call from any thread; each call to
    .show() runs the actual popup on a short-lived background thread so it
    never blocks the caller (important since some backends are blocking).
    """

    APP_NAME = "SIRA"
    DEFAULT_ICON = None  # optional path to a .ico/.png for the toast icon

    def __init__(self, icon_path: str | None = None):
        self.icon_path = icon_path or self.DEFAULT_ICON
        self._win_toaster = _Win10ToastNotifier() if _win10toast_available else None

    def show(self, title: str, message: str, duration: int = 8, on_click=None):
        """
        Fire a toast notification. Non-blocking.
        `on_click` (Windows/win10toast only) is called if the user clicks the toast.
        """
        thread = threading.Thread(
            target=self._show_sync,
            args=(title, message, duration, on_click),
            daemon=True,
        )
        thread.start()

    def _show_sync(self, title: str, message: str, duration: int, on_click):
        try:
            if self._win_toaster is not None:
                self._win_toaster.show_toast(
                    title,
                    message,
                    icon_path=self.icon_path,
                    duration=duration,
                    threaded=True,
                    callback_on_click=on_click,
                )
                return

            if _plyer_notification is not None:
                _plyer_notification.notify(
                    title=title,
                    message=message,
                    app_name=self.APP_NAME,
                    app_icon=self.icon_path or "",
                    timeout=duration,
                )
                return

            # Last-resort fallback so something is still visible in dev environments
            # without a notification backend installed.
            print(f"[Toast] {title}: {message}")

        except Exception as exc:
            print(f"[ToastNotifier] failed to show toast: {exc}")
