"""
/voice routes - powers the 'Voice: Welcome back. I detected an anomaly.'
step and lets the frontend send spoken user input in as text (after
speech-to-text) or request SYRA's reply as audio (text-to-speech).

NOTE: voice/ is not implemented yet in this codebase. Imports are
wrapped so the API still boots today; once voice/speech_to_text.py,
voice/text_to_speech.py and voice/greeting.py exist, this route starts
working with no changes needed elsewhere.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from api.routes import diagnosis as diagnosis_module

router = APIRouter(tags=["voice"])

try:
    from voice.speech_to_text import SpeechToText
    from voice.text_to_speech import TextToSpeech
    from voice.greeting import GreetingGenerator
    _stt = SpeechToText()
    _tts = TextToSpeech()
    _greeting = GreetingGenerator()
    _VOICE_READY = True
except ImportError:
    _stt = None
    _tts = None
    _greeting = None
    _VOICE_READY = False


class SynthesizeRequest(BaseModel):
    text: str


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Converts a recorded user utterance into text for /chat/message."""
    if not _VOICE_READY:
        raise HTTPException(status_code=503, detail="Voice module is not implemented yet (voice/speech_to_text.py)")

    audio_bytes = await audio.read()
    text = _stt.transcribe(audio_bytes)
    return {"text": text}


@router.post("/synthesize")
def synthesize(payload: SynthesizeRequest):
    """Converts SYRA's text reply into speech audio for the frontend to play."""
    if not _VOICE_READY:
        raise HTTPException(status_code=503, detail="Voice module is not implemented yet (voice/text_to_speech.py)")

    audio_bytes = _tts.synthesize(payload.text)
    return {"audio_base64": audio_bytes}


@router.get("/greeting")
def get_greeting():
    """
    Step: 'User opens SYRA -> Voice: Welcome back. I detected an
    anomaly.' Builds the greeting line based on whether an anomaly is
    currently on record.
    """
    if not _VOICE_READY:
        raise HTTPException(status_code=503, detail="Voice module is not implemented yet (voice/greeting.py)")

    latest = diagnosis_module._latest_diagnosis
    has_anomaly = bool(latest and latest.get("root_cause"))
    greeting_text = _greeting.generate(has_anomaly=has_anomaly, diagnosis=latest)
    return {"text": greeting_text, "has_anomaly": has_anomaly}
