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
import json
from contextlib import asynccontextmanager

# Ensure both the workspace root and backend/ are on sys.path so imports work
# regardless of whether the app is launched from the repo root or backend/.
_WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
for path in (_WORKSPACE_ROOT, _BACKEND_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database.migrations import run_migrations
from database.database import SessionLocal
from database.crud import save_metric, get_metric_count
from api.routes.metrics import router as metrics_router, record_snapshot
from api.routes import diagnosis as diagnosis_module
from api.routes.diagnosis import router as diagnosis_router
from api.routes.remediation import router as remediation_router
from api.routes.chat import router as chat_router
from api.routes.voice import router as voice_router
from api.routes.history import router as history_router
from api.routes.incidents import router as incidents_router

# Agent collectors
from agent.collectors.cpu_collector import CPUCollector
from agent.collectors.memory_collector import MemoryCollector
from agent.collectors.disk_collector import DiskCollector
from agent.collectors.network_collector import NetworkCollector
from agent.collectors.process_collector import ProcessCollector
from agent.collectors.windows_event_collector import WindowsEventCollector
from agent.event_generator import EventGenerator
from ml.inference.inference_engine import InferenceEngine
from preprocessing.cleaner import DataCleaner
from preprocessing.feature_engineering import FeatureEngineer
from reasoning.root_cause_engine import RootCauseEngine


# ── Background Agent ──────────────────────────────────────────────────────────

class BackgroundAgent:
    """Runs collectors on a loop and pushes snapshots to the metrics route."""

    def __init__(self, interval: int = 5):
        self.interval = interval
        self._running = False
        self._thread = None
        self.event_gen = EventGenerator()
        self.inference_engine = InferenceEngine()
        self.root_cause_engine = RootCauseEngine()
        self.cleaner = DataCleaner()
        self.feature_engineer = FeatureEngineer()
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

                # Persist the collected snapshot. The model-training job
                # (ml/training/train.py) uses these rows to build its dataset.
                process_data = snapshot.get("processes", {})
                top_processes = process_data.get("top_processes", [])
                top_process = top_processes[0].get("name") if top_processes else None
                db = SessionLocal()
                try:
                    saved_metric = save_metric(
                        db,
                        cpu=snapshot.get("cpu", {}).get("cpu_percent", 0.0),
                        memory=snapshot.get("memory", {}).get("memory_percent", 0.0),
                        disk=snapshot.get("disk", {}).get("disk_percent", 0.0),
                        network=snapshot.get("network", {}).get("bytes_sent", 0.0),
                        process_name=top_process,
                    )
                    database_output = {
                        "metric_id": saved_metric.id,
                        "total_snapshots": get_metric_count(db),
                    }
                finally:
                    db.close()

                record_snapshot(snapshot)

                # Preprocess -> LSTM autoencoder/anomaly detector -> failure
                # predictor -> root-cause reasoning. InferenceEngine owns the
                # rolling sequence buffer required by the LSTM.
                cleaned_snapshot = self.cleaner.clean(snapshot)
                feature_vector = self.feature_engineer.transform(cleaned_snapshot)
                inference_output = self.inference_engine.process_snapshot(snapshot)
                anomaly_info = {
                    "score": inference_output.get("anomaly_score", 0.0),
                    "affected_metric": inference_output.get("top_contributor"),
                }
                reasoning_result = self.root_cause_engine.diagnose(
                    snapshot, anomaly_info=anomaly_info
                )
                reasoning_output = {
                    key: value for key, value in reasoning_result.items() if key != "graph"
                }
                reasoning_output["timestamp"] = snapshot.get("timestamp")
                diagnosis_module._latest_diagnosis = reasoning_output

                # One JSON document per collection cycle makes the complete
                # live pipeline observable from the backend terminal.
                pipeline_output = {
                    "timestamp": snapshot.get("timestamp"),
                    "collection": snapshot,
                    "database": database_output,
                    "preprocessing": {
                        "cleaned_snapshot": cleaned_snapshot,
                        "feature_names": self.feature_engineer.feature_names(),
                        "feature_vector": feature_vector,
                    },
                    "ml_inference": inference_output,
                    "reasoning": reasoning_output,
                }
                print(
                    "[SYRA Pipeline] Live output:\n"
                    f"{json.dumps(pipeline_output, indent=2, default=str)}",
                    flush=True,
                )
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
app.include_router(incidents_router, prefix="/api/incidents", tags=["Incidents"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "SYRA"}


@app.get("/api/pipeline/status")
def pipeline_status():
    """Safe, human-readable view of the currently wired data pipeline."""
    return {
        "flow": [
            "agent", "database", "preprocessing", "ml", "reasoning", "remediation", "llm"
        ],
        "stages": {
            "agent": "active: collectors create a snapshot every polling interval",
            "database": "active: every collected snapshot is saved to SQLite",
            "preprocessing": "active: each live snapshot is cleaned and transformed into an ML feature vector",
            "ml": "active: the inference engine runs the LSTM anomaly detector and failure predictor for every snapshot",
            "training": "offline: run backend/ml/training/train.py to retrain the LSTM from saved database telemetry",
            "reasoning": "active: root-cause reasoning runs after every live ML inference",
            "remediation": "on demand: /api/remediation/propose, /approve, /execute, and /verify",
            "llm": "on demand: POST /api/chat/message produces an explanation from the latest diagnosis",
        },
        "llm": {
            "provider": "NVIDIA NIM",
            "base_url": settings.NVIDIA_BASE_URL,
            "model": settings.NVIDIA_MODEL,
            "api_key_configured": bool(settings.NVIDIA_API_KEY),
        },
    }


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print(f"[SYRA] Starting on http://{settings.HOST}:{settings.PORT}")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=False)
