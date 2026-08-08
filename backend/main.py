"""
SYRA Main Entry Point
======================
Starts the FastAPI server with:
  - All API routes (metrics, diagnosis, remediation, chat, voice, history)
  - Background monitoring agent (collectors + ML pipeline)
  - Database migrations

Run:
    cd backend
    python main.py
"""

import sys
import os
import time
import threading
from contextlib import asynccontextmanager

# Ensure backend/ is on sys.path so bare imports work
# (e.g. `from reasoning.root_cause_engine import ...`)
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.migrations import run_migrations
from api.routes.metrics import router as metrics_router, record_snapshot
from api.routes.diagnosis import router as diagnosis_router
from api.routes.remediation import router as remediation_router
from api.routes.chat import router as chat_router
from api.routes.voice import router as voice_router
from api.routes.history import router as history_router

# Agent collectors
from agent.collectors.cpu_collector import CPUCollector
from agent.collectors.memory_collector import MemoryCollector
from agent.collectors.disk_collector import DiskCollector
from agent.collectors.network_collector import NetworkCollector
from agent.collectors.process_collector import ProcessCollector
from agent.collectors.windows_event_collector import WindowsEventCollector
from agent.event_generator import EventGenerator


# ── Background Agent ──────────────────────────────────────────────────────────

class BackgroundAgent:
    """Runs collectors on a loop and pushes snapshots to the metrics route."""

    def __init__(self, interval: int = 5):
        self.interval = interval
        self._running = False
        self._thread = None
        self.event_gen = EventGenerator()
        self.collectors = {
            "cpu": CPUCollector(),
            "memory": MemoryCollector(),
            "disk": DiskCollector(),
            "network": NetworkCollector(),
            "process": ProcessCollector(),
            "windows_event": WindowsEventCollector(),
        }

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"[Agent] Started (interval={self.interval}s)")

    def stop(self):
        self._running = False
        print("[Agent] Stopped")

    def _loop(self):
        while self._running:
            try:
                snapshot = self.event_gen.generate(
                    self.collectors["cpu"].collect(),
                    self.collectors["memory"].collect(),
                    self.collectors["disk"].collect(),
                    self.collectors["network"].collect(),
                    self.collectors["process"].collect(),
                    self.collectors["windows_event"].collect(),
                )
                record_snapshot(snapshot)
            except Exception as e:
                print(f"[Agent] Error: {e}")
            time.sleep(self.interval)


agent = BackgroundAgent(interval=settings.AGENT_POLL_INTERVAL)


# ── App Lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    agent.start()
    print("[SYRA] Server is ready")
    yield
    agent.stop()
    print("[SYRA] Shutting down")


# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="SYRA",
    description="System Your Reliable Assistant — AI-powered computer health monitor",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(metrics_router, prefix="/api/metrics", tags=["Metrics"])
app.include_router(diagnosis_router, prefix="/api/diagnosis", tags=["Diagnosis"])
app.include_router(remediation_router, prefix="/api/remediation", tags=["Remediation"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(voice_router, prefix="/api/voice", tags=["Voice"])
app.include_router(history_router, prefix="/api/history", tags=["History"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "SYRA"}


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print(f"[SYRA] Starting on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=False)
