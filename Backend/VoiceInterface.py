"""
VoiceInterface.py — Clean, reliable voice listener with conversation mode.
Uses threading.Timer for conversation timeout — no hacky timestamp checking.
"""
import time
import threading
import speech_recognition as sr
from Backend.Logger import logger

CONVERSATION_TIMEOUT = 25  # seconds of silence before dropping back to wake-word mode


class ContinuousListener:
    """
    Listens for the wake word 'Jarvis'.
    Once heard, enters conversation mode — any speech is processed as a command.
    After CONVERSATION_TIMEOUT seconds of inactivity, returns to passive mode.
    """

    def __init__(self, wake_word: str = "jarvis"):
        self.wake_word = wake_word.lower()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_paused = False
        self.in_conversation = False
        self._timer: threading.Timer | None = None

        # Tuned for speed and reliability
        self.recognizer.pause_threshold = 0.8      # 0.8s silence = end of phrase
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = False

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.3)

    # ── Pause / Resume ──────────────────────────────────────────────────────

    def pause(self):
        self.is_paused = True
        logger.info("Listener paused.")

    def resume(self):
        """Called by Jarvis.py after TTS finishes. Restarts the conversation timer."""
        self.is_paused = False
        if self.in_conversation:
            self._reset_timer()   # 25s window starts NOW (after JARVIS finishes speaking)
        logger.info("Listener resumed.")

    # ── Conversation timer ───────────────────────────────────────────────────

    def _reset_timer(self):
        """Cancel existing timer and start a fresh CONVERSATION_TIMEOUT countdown."""
        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(CONVERSATION_TIMEOUT, self._end_conversation)
        self._timer.daemon = True
        self._timer.start()

    def _end_conversation(self):
        self.in_conversation = False
        self._timer = None
        logger.info("Conversation ended. Back to wake-word mode.")
        print("JARVIS_UI|STATUS|Listening...")

    def _start_conversation(self):
        self.in_conversation = True
        self._reset_timer()

    # ── Main loop ────────────────────────────────────────────────────────────

    def listen_for_wake_word(self, callback_on_wake):
        logger.info("Background Listener Active. Waiting for wake word.")

        while True:
            # While JARVIS is speaking / processing, wait here
            if self.is_paused:
                time.sleep(0.05)
                continue

            try:
                with self.microphone as source:
                    if self.in_conversation:
                        print("JARVIS_UI|STATUS|Awaiting command...")
                    else:
                        print("JARVIS_UI|STATUS|Listening...")

                    # No timeout — blocks until speech is detected.
                    # Conversation expiry is handled by threading.Timer in background.
                    audio = self.recognizer.listen(source, phrase_time_limit=12)

                # Skip if paused while we were listening
                if self.is_paused:
                    continue

                text = self.recognizer.recognize_google(
                    audio, language='en-IN'
                ).lower()
                logger.info(f"Heard: {text}")

                if self.in_conversation:
                    # ── Conversation mode: process anything spoken ──────────
                    logger.info(f"Executing conversation command: {text}")
                    self._reset_timer()          # reset 25s window on each command
                    self.pause()
                    callback_on_wake(text)

                else:
                    # ── Passive mode: wait for wake word ────────────────────
                    if self.wake_word in text:
                        logger.info("Wake word detected!")
                        print("JARVIS_UI|STATUS|Processing command...")

                        parts = text.split(self.wake_word, 1)
                        command = parts[1].strip() if len(parts) > 1 else ""

                        self._start_conversation()
                        self.pause()

                        if command:
                            logger.info(f"Inline command: {command}")
                            callback_on_wake(command)
                        else:
                            logger.info("Wake word only — greeting.")
                            callback_on_wake("hello jarvis")

            except sr.UnknownValueError:
                # Could not understand audio — just continue
                continue
            except sr.RequestError as e:
                logger.error(f"Speech recognition error: {e}")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Listener error: {e}")
                time.sleep(0.5)
