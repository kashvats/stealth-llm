import threading
import asyncio
import logging
import tkinter as tk
import os
import sys
import pyperclip
from queue import Queue
from dotenv import load_dotenv

from overlay import StealthOverlay
from clipboard_monitor import ClipboardMonitor
from llm_client import OllamaClient, OpenAIClient, MockLLMClient
from audio_transcriber import AudioTranscriber
from lock_manager import LockManager, LockState
from hotkey_listener import GlobalHotkeyListener

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StealthPilotApp:
    def __init__(self):
        self.root = tk.Tk()
        
        # Lock Manager
        self.lock_manager = LockManager(on_state_change=self._handle_lock_change)
        
        # Clients
        local_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.ollama_client = OllamaClient(model=local_model)
        self.current_client = self.ollama_client
        
        # UI
        self.overlay = StealthOverlay(self.root)
        self.ui_queue = Queue()
        
        # Audio
        self.audio_transcriber = AudioTranscriber(
            model_size="tiny.en",
            on_partial=self._on_partial_speech,
            on_final=self._handle_final_speech,
            on_volume=self._on_volume
        )
        
        # Hotkeys
        self.hotkeys = GlobalHotkeyListener({
            'toggle_listen': self.toggle_listen,
            'close': self.root.quit,
            'copy_paste': self.trigger_copy_paste,
            'dsa_mode': self.trigger_dsa_mode,
            'absolute_lock': lambda: self.lock_manager.set_state(LockState.ABSOLUTE_LOCK),
            'unlock': lambda: self.lock_manager.try_unlock(force=True),
            'toggle_language': self.toggle_language,
            'rescan_audio': self.rescan_audio,
            'emergency_stop': self.emergency_stop
        })

        self.clipboard_monitor = ClipboardMonitor(callback=self._on_clipboard_change)
        self.listening = True
        self.language = "Python"
        self.overlay.set_language_indicator(self.language)

    def _handle_lock_change(self, state):
        self.overlay.set_lock_indicator(state.name)
        if state != LockState.UNLOCKED:
            self.audio_transcriber.pause()
        else:
            if self.listening:
                self.audio_transcriber.resume()

    def _on_partial_speech(self, text: str):
        if not self.lock_manager.is_locked():
            self.ui_queue.put(("caption", text, False))

    def _handle_final_speech(self, text: str):
        if self.lock_manager.is_locked():
            return
        self.ui_queue.put(("caption", text, True))
        # Simple Tech Answer Mode: Auto-trigger on sentence if not locked
        self.handle_question(text)

    def _on_clipboard_change(self, text: str):
        if self.lock_manager.is_locked():
            return
        # Copy-Paste Mode usually triggered by V, but monitor can also trigger
        # unless rules state ONLY V. Plan says: Trigger: V or clipboard change.
        self.trigger_copy_paste(text)

    def trigger_copy_paste(self, text: str = None):
        if not text:
            text = pyperclip.paste()
        self.lock_manager.set_state(LockState.NORMAL_LOCK)
        self.handle_question(text)

    def trigger_dsa_mode(self, text: str = None):
        if not text:
            text = pyperclip.paste()
        self.lock_manager.set_state(LockState.NORMAL_LOCK)
        prompt = f"DSA coding problem. Language: {self.language}. Provide professional explanation and implementation. \n\nProblem: {text}"
        self.handle_question(prompt, mode="DSA")

    def handle_question(self, question: str, mode="TECH"):
        logger.info(f"Processing {mode} request: {question[:50]}...")
        self.ui_queue.put("Thinking...")
        self.audio_transcriber.pause() # Pause during processing/display
        threading.Thread(target=self._ask_llm, args=(question, mode)).start()

    def _ask_llm(self, question: str, mode="TECH"):
        try:
            with open("system_prompt.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except:
            system_prompt = "You are a professional software engineer."

        if mode == "DSA":
            system_prompt = f"You are a DSA expert. Provide a professional explanation of the concept and approach followed by a clean {self.language} implementation."

        answer = self.current_client.ask(question, system_prompt=system_prompt)
        
        # Ensure final token
        if not answer.strip().endswith("[X]"):
            answer = answer.strip() + " [X]"
            
        self.ui_queue.put(answer)
        
        # Normal Lock auto-unlocks after generation
        if self.lock_manager.state == LockState.NORMAL_LOCK:
            self.lock_manager.try_unlock()
        
        # Resume listening if we were in Live mode and not locked
        if not self.lock_manager.is_locked() and self.listening:
            # We wait a bit to let the user read? Or just resume?
            # Requirement says "Assistant-generated output must never re-enter capture path"
            # Since it's text, it won't. But if we had TTS, we'd wait.
            # We'll resume after a short delay to be safe.
            threading.Timer(1.0, self.audio_transcriber.resume).start()

    def toggle_listen(self):
        self.listening = not self.listening
        if self.listening:
            self.audio_transcriber.resume()
            self.overlay.show("Listening ON", 2)
        else:
            self.audio_transcriber.pause()
            self.overlay.show("Listening OFF", 2)

    def _on_volume(self, level):
        self.ui_queue.put(("volume", level))

    def toggle_language(self):
        if self.language == "Python":
            self.language = "Auto"
        else:
            self.language = "Python"
        self.overlay.set_language_indicator(self.language)
        self.overlay.show(f"Language: {self.language}", 2)
        logger.info(f"Language toggled to: {self.language}")

    def rescan_audio(self):
        logger.info("Manual Audio Rescan Triggered...")
        self.audio_transcriber.stop()
        self.audio_transcriber.start()
        self.overlay.show("Rescanning Audio...", 2)

    def emergency_stop(self):
        logger.warning("Emergency Stop: Terminating...")
        self.audio_transcriber.stop()
        self.hotkeys.stop()
        self.root.destroy()
        os._exit(0)

    def process_ui_queue(self):
        while not self.ui_queue.empty():
            item = self.ui_queue.get()
            if isinstance(item, tuple) and item[0] == "caption":
                _, text, is_final = item
                self.overlay.update_caption(text, is_final)
            elif item[0] == "volume":
                self.overlay.update_meter(item[1])
            else:
                self.overlay.update_text(item)
        self.root.after(100, self.process_ui_queue)

    def run(self):
        self.hotkeys.start()
        threading.Thread(target=self.clipboard_monitor.start, daemon=True).start()
        self.audio_transcriber.start()
        self.root.after(100, self.process_ui_queue)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.emergency_stop()

if __name__ == "__main__":
    app = StealthPilotApp()
    app.run()
