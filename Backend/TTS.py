"""
TTS.py — JARVIS Text-to-Speech
Uses a dedicated worker thread that owns pyttsx3 permanently.
This avoids Windows COM threading issues entirely.
SpeakJarvis() is safe to call from any thread.
"""
import re
import queue
import threading
import unicodedata
import pyttsx3

# ---------------------------------------------------------------------------
# Worker thread — owns the pyttsx3 engine forever
# ---------------------------------------------------------------------------

_tts_queue = queue.Queue()
_done_event = threading.Event()   # signals caller that speech finished


def _tts_worker():
    """Runs in its own daemon thread. Owns the pyttsx3 engine."""
    engine = pyttsx3.init()
    engine.setProperty('rate', 200)
    engine.setProperty('volume', 1.0)

    # Pick best male voice (David / Mark on Windows)
    voices = engine.getProperty('voices')
    for v in voices:
        if any(p in v.name.lower() for p in ['david', 'mark', 'george', 'male']):
            engine.setProperty('voice', v.id)
            break

    while True:
        text = _tts_queue.get()      # blocks until SpeakJarvis puts something here
        if text is None:             # None = shutdown signal (never sent in practice)
            break
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"TTS worker error: {e}")
        finally:
            _done_event.set()        # unblock the caller


# Start the worker thread once at import time
_worker_thread = threading.Thread(target=_tts_worker, daemon=True, name="TTS-Worker")
_worker_thread.start()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Remove emojis and non-speech characters, normalise whitespace."""
    normalized = unicodedata.normalize('NFKD', text)
    cleaned = ''.join(
        ch for ch in normalized
        if not unicodedata.category(ch).startswith(('So', 'Cs', 'Co'))
    )
    cleaned = re.sub(r'[^\w\s.,!?:;\'\"-]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def SpeakJarvis(text: str, callback_func=None):
    """
    Speak text using the dedicated TTS worker thread.
    Blocks the calling thread until speech is finished.
    Safe to call from any thread.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return

    # Trim very long responses — speak the first 2 sentences only
    if len(cleaned) > 400:
        sentences = re.split(r'(?<=[.!?])\s+', cleaned)
        cleaned = ' '.join(sentences[:2]) if len(sentences) > 2 else cleaned[:400]

    _done_event.clear()
    _tts_queue.put(cleaned)
    _done_event.wait()          # wait until the worker thread finishes speaking
