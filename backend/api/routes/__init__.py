from .metrics import router as metrics_router
from .diagnosis import router as diagnosis_router
from .remediation import router as remediation_router
from .chat import router as chat_router
from .voice import router as voice_router
from .history import router as history_router

__all__ = [
    "metrics_router",
    "diagnosis_router",
    "remediation_router",
    "chat_router",
    "voice_router",
    "history_router",
]
