"""
SYRA LLM Subsystem
------------------
Natural language generation powered by Llama 3.1 70B Instruct via NVIDIA NIM.

Usage:
    from backend.llm import SyraChatEngine
    engine = SyraChatEngine()
    response = engine.chat("What's wrong with my computer?")
"""

from .provider import LLMProvider
from .prompts import SYSTEM_PROMPT
from .explanation import ExplanationEngine
from .conversation_memory import ConversationMemory
from .response_formatter import ResponseFormatter
from .memory import SyraChatEngine

__all__ = [
    "LLMProvider",
    "SYSTEM_PROMPT",
    "ExplanationEngine",
    "ConversationMemory",
    "ResponseFormatter",
    "SyraChatEngine",
]
