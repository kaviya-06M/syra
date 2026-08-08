import os
import shutil
import tempfile

import psutil


class RemediationActions:
    """
    Library of concrete fix actions that ExecutorEngine can run once the
    user has granted permission. Every action returns a result dict
    describing what happened, so it can be logged, shown in the UI, and
    used later by the Verifier / RollbackManager.
    """

    def kill_top_process(self, pid=None):
        """Terminates the highest CPU-consuming process, or a specific
        pid if one is provided."""
        target = None

        if pid is not None:
            try:
                target = psutil.Process(pid)
            except psutil.NoSuchProcess:
                return {"success": False, "action": "kill_top_process",
                        "message": f"Process {pid} not found"}
        else:
            candidates = sorted(
                psutil.process_iter(["pid", "name", "cpu_percent"]),
                key=lambda p: p.info.get("cpu_percent") or 0,
                reverse=True
            )
            if candidates:
                target = candidates[0]

        if target is None:
            return {"success": False, "action": "kill_top_process",
                     "message": "No target process found"}

        try:
            snapshot = {"pid": target.pid, "name": target.name()}
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

    def clear_temp_files(self):
        """Deletes files inside the OS temp directory to free up disk space."""
        temp_dir = tempfile.gettempdir()
        freed_bytes = 0
        removed = 0
        errors = 0

        for entry in os.listdir(temp_dir):
            path = os.path.join(temp_dir, entry)
            try:
                if os.path.isfile(path):
                    freed_bytes += os.path.getsize(path)
                    os.remove(path)
                    removed += 1
                elif os.path.isdir(path):
                    freed_bytes += self._dir_size(path)
                    shutil.rmtree(path, ignore_errors=True)
                    removed += 1
            except Exception:
                errors += 1
                continue

        return {
            "success": True,
            "action": "clear_temp_files",
            "message": f"Removed {removed} temp items, freed ~{freed_bytes / (1024 * 1024):.1f} MB",
            "freed_bytes": freed_bytes,
            "errors": errors
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
            os.system(f"net stop {service_name}")
            start = os.system(f"net start {service_name}")
            success = start == 0
            return {
                "success": success,
                "action": "restart_service",
                "message": f"Service '{service_name}' restarted" if success else f"Failed to restart '{service_name}'",
                "target": {"service_name": service_name}
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
