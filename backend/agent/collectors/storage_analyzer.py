import os
import time
import threading
from pathlib import Path


class StorageAnalyzer:
    """
    Scans and analyzes disk space usage across major user and system directories
    (Videos, Pictures, Downloads, Documents, Temp, Program Files, etc.) with
    non-blocking background caching.
    """

    def __init__(self, cache_ttl_seconds: int = 120):
        self.cache_ttl = cache_ttl_seconds
        self.last_scanned_time = 0.0
        self.cached_breakdown = []
        self._is_scanning = False
        self._lock = threading.Lock()

    def _get_dir_size(self, path: str, max_depth: int = 3) -> int:
        """Calculate total directory size in bytes safely, avoiding recursive permission errors."""
        total = 0
        try:
            p = Path(path)
            if not p.exists() or not p.is_dir():
                return 0

            # Scan files with depth limit for high performance
            for root, dirs, files in os.walk(path):
                # Calculate current depth relative to start path
                rel = os.path.relpath(root, path)
                depth = 0 if rel == "." else len(rel.split(os.sep))
                if depth > max_depth:
                    dirs.clear()  # Don't recurse deeper
                    continue

                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        if not os.path.islink(fp):
                            total += os.path.getsize(fp)
                    except (OSError, PermissionError):
                        continue
        except Exception:
            pass
        return total

    def _format_size(self, bytes_val: int) -> str:
        if bytes_val >= 1024 ** 4:
            return f"{bytes_val / (1024 ** 4):.1f} TB"
        if bytes_val >= 1024 ** 3:
            return f"{bytes_val / (1024 ** 3):.1f} GB"
        if bytes_val >= 1024 ** 2:
            return f"{bytes_val / (1024 ** 2):.1f} MB"
        if bytes_val >= 1024:
            return f"{bytes_val / 1024:.1f} KB"
        return f"{bytes_val} B"

    def scan(self) -> list[dict]:
        """Runs a scan of standard user profile folders and system locations."""
        home = Path.home()
        local_app_data = os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local"))
        temp_dir = os.environ.get("TEMP", os.path.join(local_app_data, "Temp"))

        targets = [
            {"name": "Videos", "path": str(home / "Videos"), "type": "user_media"},
            {"name": "Pictures", "path": str(home / "Pictures"), "type": "user_media"},
            {"name": "Downloads", "path": str(home / "Downloads"), "type": "user_downloads"},
            {"name": "Documents", "path": str(home / "Documents"), "type": "user_docs"},
            {"name": "Desktop", "path": str(home / "Desktop"), "type": "user_desktop"},
            {"name": "Music", "path": str(home / "Music"), "type": "user_media"},
            {"name": "Temporary Files & Cache", "path": temp_dir, "type": "system_cache"},
            {"name": "Program Files", "path": r"C:\Program Files", "type": "apps"},
            {"name": "Program Files (x86)", "path": r"C:\Program Files (x86)", "type": "apps"},
        ]

        results = []
        for t in targets:
            path_str = t["path"]
            if os.path.exists(path_str):
                size_bytes = self._get_dir_size(path_str, max_depth=3)
                size_gb = round(size_bytes / (1024 ** 3), 2)
                results.append({
                    "name": t["name"],
                    "path": path_str,
                    "type": t["type"],
                    "size_bytes": size_bytes,
                    "size_gb": size_gb,
                    "size_formatted": self._format_size(size_bytes),
                })

        # Sort descending by size
        results.sort(key=lambda x: x["size_bytes"], reverse=True)
        return results

    def get_breakdown(self, force_refresh: bool = False) -> list[dict]:
        """Returns the storage breakdown, utilizing cache or spawning non-blocking scan."""
        now = time.time()
        with self._lock:
            if not self.cached_breakdown or force_refresh or (now - self.last_scanned_time > self.cache_ttl):
                # If first time or force_refresh, scan synchronously once
                if not self.cached_breakdown:
                    self.cached_breakdown = self.scan()
                    self.last_scanned_time = now
                elif not self._is_scanning:
                    # Refresh asynchronously in background thread so collector never blocks
                    self._is_scanning = True
                    def _bg_scan():
                        try:
                            fresh = self.scan()
                            with self._lock:
                                self.cached_breakdown = fresh
                                self.last_scanned_time = time.time()
                        finally:
                            self._is_scanning = False
                    threading.Thread(target=_bg_scan, daemon=True).start()

            return self.cached_breakdown
