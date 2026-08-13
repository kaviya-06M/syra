import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import psutil


class RemediationActions:
    """
    Library of concrete fix actions that ExecutorEngine can run once the
    user has granted permission. Every action returns a result dict
    describing what happened, so it can be logged, shown in the UI, and
    used later by the Verifier / RollbackManager.
    """

    PROTECTED_PROCESS_NAMES = {
        "csrss.exe", "explorer.exe", "lsass.exe", "services.exe", "smss.exe",
        "system", "system idle process", "wininit.exe", "winlogon.exe",
        "memcompression", "registry", "svchost.exe", "dwm.exe", "spoolsv.exe",
        "fontdrvhost.exe", "sihost.exe", "taskhostw.exe", "ctfmon.exe",
        "tiworker.exe", "trustedinstaller.exe", "msmpeng.exe", "searchindexer.exe",
        "taskmgr.exe", "antigravity ide.exe",
    }

    BROWSER_PROCESS_NAMES = {
        "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe",
    }

    @classmethod
    def is_protected_process(cls, name):
        return str(name or "").casefold() in cls.PROTECTED_PROCESS_NAMES

    @classmethod
    def is_browser_process(cls, name):
        return str(name or "").casefold() in cls.BROWSER_PROCESS_NAMES

    def close_browser_tab(self, pid=None, expected_name=None):
        """Send Ctrl+W to the approved browser window.

        psutil can terminate processes, but it cannot address browser tabs.
        This Windows-only action finds a visible top-level window owned by
        the approved browser process (or one of its parents), focuses it,
        and sends the standard close-tab shortcut. It never terminates the
        browser process.
        """
        if os.name != "nt":
            return {"success": False, "action": "close_browser_tab", "message": "Closing a browser tab is supported on Windows only"}
        if pid is None:
            return {"success": False, "action": "close_browser_tab", "message": "An approved browser PID is required"}

        try:
            process = psutil.Process(int(pid))
            name = process.name()
            if expected_name and name.casefold() != str(expected_name).casefold():
                return {"success": False, "action": "close_browser_tab", "message": "Target browser no longer matches the approved process"}
            if not self.is_browser_process(name):
                return {"success": False, "action": "close_browser_tab", "message": f"{name} is not a supported browser process"}

            window = self._find_browser_window(process)
            if window is None:
                return {"success": False, "action": "close_browser_tab", "message": "No visible browser window was found for the approved process"}

            user32 = __import__("ctypes").windll.user32
            if not user32.SetForegroundWindow(window):
                return {"success": False, "action": "close_browser_tab", "message": "Windows did not allow SYRA to focus the approved browser window"}
            time.sleep(0.15)
            # VK_CONTROL=0x11, VK_W=0x57, KEYEVENTF_KEYUP=0x0002
            user32.keybd_event(0x11, 0, 0, 0)
            user32.keybd_event(0x57, 0, 0, 0)
            user32.keybd_event(0x57, 0, 0x0002, 0)
            user32.keybd_event(0x11, 0, 0x0002, 0)
            return {
                "success": True,
                "action": "close_browser_tab",
                "message": f"Sent Ctrl+W to the approved {name} browser window",
                "target": {"pid": process.pid, "name": name, "window_handle": int(window)},
            }
        except psutil.NoSuchProcess:
            return {"success": False, "action": "close_browser_tab", "message": f"Browser process {pid} no longer exists"}
        except Exception as exc:
            return {"success": False, "action": "close_browser_tab", "message": str(exc)}

    def _find_browser_window(self, process):
        """Return a visible window handle owned by the process or its parents."""
        import ctypes
        import ctypes.wintypes

        owners = {process.pid}
        current = process
        for _ in range(8):
            try:
                parent = current.parent()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
            if parent is None or parent.pid in owners:
                break
            owners.add(parent.pid)
            current = parent

        found = []
        enum_callback = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        def callback(hwnd, _lparam):
            if not ctypes.windll.user32.IsWindowVisible(hwnd):
                return True
            owner_pid = ctypes.wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner_pid))
            if owner_pid.value in owners:
                found.append(hwnd)
                return False
            return True

        ctypes.windll.user32.EnumWindows(enum_callback(callback), 0)
        return found[0] if found else None

    def kill_top_process(self, pid=None, expected_name=None):
        """Terminates only the process PID/name that was approved."""
        if pid is None:
            return {"success": False, "action": "kill_top_process", "message": "An approved PID is required"}
        target = None

        try:
            target = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return {"success": False, "action": "kill_top_process", "message": f"Process {pid} not found"}

        if target is None:
            return {"success": False, "action": "kill_top_process",
                     "message": "No target process found"}

        try:
            snapshot = {"pid": target.pid, "name": target.name()}
            if self.is_protected_process(snapshot["name"]):
                return {"success": False, "action": "kill_top_process", "message": "Protected system process cannot be terminated"}
            if expected_name and snapshot["name"].casefold() != expected_name.casefold():
                return {"success": False, "action": "kill_top_process", "message": "Target PID no longer matches the approved process"}
            target.terminate()
            target.wait(timeout=3)
            return {
                "success": True,
                "action": "kill_top_process",
                "message": f"Terminated process {snapshot['name']} (pid {snapshot['pid']})",
                "target": snapshot
            }
        except Exception as e:
            return {"success": False, "action": "kill_top_process", "message": str(e)}

    def lower_process_priority(self, pid=None, expected_name=None):
        """Lower an approved process's priority without terminating it."""
        if pid is None:
            return {"success": False, "action": "lower_process_priority", "message": "An approved PID is required"}
        try:
            target = psutil.Process(pid)
            name = target.name()
            if self.is_protected_process(name):
                return {"success": False, "action": "lower_process_priority", "message": "Protected system process cannot be modified"}
            if expected_name and name.casefold() != expected_name.casefold():
                return {"success": False, "action": "lower_process_priority", "message": "Target PID no longer matches the approved process"}
            previous_priority = target.nice()
            new_priority = psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else min(int(previous_priority) + 5, 19)
            target.nice(new_priority)
            return {
                "success": True,
                "action": "lower_process_priority",
                "message": f"Lowered priority for {name} (pid {pid})",
                "target": {"pid": pid, "name": name},
                "previous_priority": previous_priority,
                "new_priority": new_priority,
            }
        except Exception as exc:
            return {"success": False, "action": "lower_process_priority", "message": str(exc)}

    def clear_temp_files(self, rollback_id=None):
        """Moves temp items to SYRA quarantine so verification can undo cleanup."""
        temp_dir = tempfile.gettempdir()
        freed_bytes = 0
        quarantined = []
        errors = 0
        quarantine_root = Path(__file__).resolve().parent / "quarantine"
        quarantine_dir = quarantine_root / (rollback_id or "manual")
        quarantine_dir.mkdir(parents=True, exist_ok=True)

        for entry in os.listdir(temp_dir):
            path = os.path.join(temp_dir, entry)
            destination = str(quarantine_dir / entry)
            try:
                if os.path.exists(destination):
                    errors += 1
                    continue
                if os.path.isfile(path) or os.path.isdir(path):
                    freed_bytes += os.path.getsize(path) if os.path.isfile(path) else self._dir_size(path)
                    shutil.move(path, destination)
                    quarantined.append({"original": path, "quarantined": destination})
            except Exception:
                errors += 1
                continue

        return {
            "success": True,
            "action": "clear_temp_files",
            "message": f"Quarantined {len(quarantined)} temp items, freed ~{freed_bytes / (1024 * 1024):.1f} MB",
            "freed_bytes": freed_bytes,
            "errors": errors,
            "rollback_data": {"quarantined_items": quarantined, "quarantine_dir": str(quarantine_dir)},
        }

    def _dir_size(self, path):
        total = 0
        for root, _, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    continue
        return total

    def flush_dns(self):
        """Flushes the Windows DNS resolver cache to fix network issues."""
        try:
            result = os.system("ipconfig /flushdns")
            return {
                "success": result == 0,
                "action": "flush_dns",
                "message": "DNS cache flushed" if result == 0 else "DNS flush failed"
            }
        except Exception as e:
            return {"success": False, "action": "flush_dns", "message": str(e)}

    def restart_service(self, service_name):
        """Restarts a named Windows service."""
        try:
            query = subprocess.run(["sc", "query", service_name], check=False, capture_output=True, text=True)
            was_running = "RUNNING" in query.stdout.upper()
            subprocess.run(["net", "stop", service_name], check=False, capture_output=True, text=True)
            start = subprocess.run(["net", "start", service_name], check=False, capture_output=True, text=True)
            success = start.returncode == 0
            return {
                "success": success,
                "action": "restart_service",
                "message": f"Service '{service_name}' restarted" if success else f"Failed to restart '{service_name}'",
                "target": {"service_name": service_name},
                "rollback_data": {"was_running": was_running},
            }
        except Exception as e:
            return {"success": False, "action": "restart_service", "message": str(e)}

    def free_memory(self):
        """Best-effort memory pressure relief by trimming the working set
        of background processes. Windows-only; safe no-op elsewhere."""
        try:
            import ctypes
            freed = 0
            for proc in psutil.process_iter(["pid"]):
                try:
                    handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.info["pid"])
                    if handle:
                        ctypes.windll.psapi.EmptyWorkingSet(handle)
                        ctypes.windll.kernel32.CloseHandle(handle)
                        freed += 1
                except Exception:
                    continue
            return {
                "success": True,
                "action": "free_memory",
                "message": f"Trimmed working set for {freed} processes"
            }
        except Exception as e:
            return {"success": False, "action": "free_memory", "message": str(e)}
