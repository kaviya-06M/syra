"""
SYRA FastAPI Server
====================
Central server that Electron connects to via localhost.
Registers all route blueprints and starts the background agent.
"""

import sys
import os
import threading

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.metrics import router as metrics_router
from backend.api.routes.diagnosis import router as diagnosis_router
from backend.api.routes.remediation import router as remediation_router
from backend.api.routes.chat import router as chat_router
from backend.api.routes.history import router as history_router

from backend.database.migrations import run_migrations


def create_app() -> FastAPI:
    """Factory function that builds and configures the SYRA FastAPI app."""

    app = FastAPI(
        title="SYRA",
        description="System Your Reliable Assistant — AI-powered computer health monitor",
        version="1.0.0",
    )

    # ── CORS (Electron renderer runs on a different origin) ───────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Database ──────────────────────────────────────────────────────────
    run_migrations()

    # ── Routes ────────────────────────────────────────────────────────────
    app.include_router(metrics_router, prefix="/api/metrics", tags=["Metrics"])
    app.include_router(diagnosis_router, prefix="/api/diagnosis", tags=["Diagnosis"])
    app.include_router(remediation_router, prefix="/api/remediation", tags=["Remediation"])
    app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
    app.include_router(history_router, prefix="/api/history", tags=["History"])

    # ── Health check ──────────────────────────────────────────────────────
    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "SYRA"}

    return app


app = create_app()
