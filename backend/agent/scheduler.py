import sys
import os
import time
import json

# Ensure agent dir and backend root are both on path
AGENT_DIR   = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(AGENT_DIR)
sys.path.insert(0, AGENT_DIR)
sys.path.insert(0, BACKEND_DIR)

from collectors.cpu_collector    import CPUCollector
from collectors.memory_collector import MemoryCollector
from collectors.disk_collector   import DiskCollector
from collectors.network_collector import NetworkCollector
from collectors.process_collector import ProcessCollector
from collectors.windows_event_collector import WindowsEventCollector

from event_generator import EventGenerator

# Database
from database.migrations import run_migrations
from database.database   import SessionLocal
from database.crud       import save_metric, get_metric_count


# ── First-run: create tables if they don't exist ──────────────────────────────
run_migrations()

# ── Collectors ────────────────────────────────────────────────────────────────
cpu_col     = CPUCollector()
memory_col  = MemoryCollector()
disk_col    = DiskCollector()
network_col = NetworkCollector()
process_col = ProcessCollector()
windows_col = WindowsEventCollector()

generator   = EventGenerator()

print("[SYRA Agent] Starting monitoring loop — saving to database every cycle...\n")

# ── Main loop ─────────────────────────────────────────────────────────────────
while True:

    cpu_data     = cpu_col.collect()
    memory_data  = memory_col.collect()
    disk_data    = disk_col.collect()
    network_data = network_col.collect()
    process_data = process_col.collect()
    windows_data = windows_col.collect()

    # Build unified event snapshot
    event = generator.generate(
        cpu_data,
        memory_data,
        disk_data,
        network_data,
        process_data,
        windows_data,
    )

    # ── Save to SQLite for ML pipeline ────────────────────────────────────────
    top_process = (
        process_data["top_processes"][0]["name"]
        if process_data.get("top_processes") else None
    )

    db = SessionLocal()
    try:
        save_metric(
            db,
            cpu     = cpu_data["cpu_percent"],
            memory  = memory_data["memory_percent"],
            disk    = disk_data["disk_percent"],
            network = network_data["bytes_sent"],
            process_name = top_process,
        )
        total = get_metric_count(db)
    finally:
        db.close()

    # ── Console output ─────────────────────────────────────────────────────────
    print(json.dumps(event, indent=2))
    print(f"\n[DB] Saved snapshot #{total} to system_metrics\n")
    print("=" * 60)

    time.sleep(5)