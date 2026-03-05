import threading
import asyncio
import logging
import tkinter as tk
import os
import sys
import pyperclip
import time
import datetime
from queue import Queue
from dotenv import load_dotenv
import json

from stealth_overlay_buttons import StealthOverlayButtons
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
        self.overlay = StealthOverlayButtons(
            self.root, 
            on_toggle_mode=self.toggle_llm_mode,
            on_voice_toggle=self.toggle_listen,
            on_paste=self.trigger_copy_paste,
            on_dsa=self.trigger_dsa_mode,
            on_clear=self.clear_context,
            on_notepad_toggle=self.toggle_lock,
            on_copy=self.copy_to_clipboard,
            on_history_prev=self.show_prev_answer,
            on_history_next=self.show_next_answer
        )
        self.ui_queue = Queue()
        self.is_online = False
        
        # History & Logging State
        self.answer_history = []  # List of dicts: {'question': str, 'answer': str}
        self.history_index = -1
        
        # Audio
        logger.info("Initializing Audio Module (Eager Loading)...")
        self.audio_transcriber = AudioTranscriber(
            model_size="tiny.en",
            on_partial=self._on_partial_speech,
            on_final=self._handle_final_speech,
            on_volume=self._on_volume
        )
        logger.info("Audio Module Initialized.")
        
        # Hotkeys
        self.hotkeys = GlobalHotkeyListener({
            'toggle_listen': self.toggle_listen,
            'close': self.root.quit,
            'copy_paste': self.trigger_copy_paste,
            'dsa_mode': self.trigger_dsa_mode,
            'absolute_lock': lambda: self.lock_manager.set_state(LockState.ABSOLUTE_LOCK),
            'unlock': lambda: self.lock_manager.try_unlock(force=True),
            'toggle_language': self.toggle_language,
            'toggle_clipboard': self.toggle_clipboard,
            'rescan_audio': self.rescan_audio,
            'emergency_stop': self.emergency_stop
        })

        self.overlay.set_lang_callback(self.set_language)
        self.overlay.set_color_callback(self.set_color)

        self.clipboard_monitor = ClipboardMonitor(callback=self._on_clipboard_change)
        self.listening = True
        self.history = []
        self.max_history = 10 
        self.clipboard_enabled = True

        self._load_config()
        # Sync Initial UI
        self.overlay.set_language_indicator(self.language)
        # Main will trigger color change on overlay if we add that callback, or just set it
        threading.Thread(target=self._delayed_sync, daemon=True).start()

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
        
        # Heuristic Trigger: questions or specific keywords
        t = text.lower()
        if "?" in t or any(k in t for k in ["tell me", "solve", "explain", "how do I"]):
            self.handle_question(text)

    def _load_config(self):
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    cfg = json.load(f)
                self.language = cfg.get("language", "Python")
                print(self.language)
                self.current_color = cfg.get("color_theme", "Green")
                self.is_online = (cfg.get("llm_mode", "cloud") == "cloud")
                if self.is_online:
                    if not hasattr(self, "openai_client"):
                        self.openai_client = OpenAIClient(
                            api_key=os.getenv("OPENAI_API_KEY"),
                            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                        )
                    self.current_client = self.openai_client
                logger.info(f"Config loaded: Lang={self.language}, Color={self.current_color}, Online={self.is_online}")
            else:
                self.language = "Python"
                self.current_color = "Green"
                self.is_online = True
                if not hasattr(self, "openai_client"):
                    self.openai_client = OpenAIClient(
                        api_key=os.getenv("OPENAI_API_KEY"),
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                    )
                self.current_client = self.openai_client
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.language = "Python"
            self.current_color = "Green"
            self.is_online = True

    def _save_config(self):
        try:
            cfg = {
                "language": self.language,
                "color_theme": self.current_color,
                "llm_mode": "cloud" if self.is_online else "local"
            }
            with open("config.json", "w") as f:
                json.dump(cfg, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def _delayed_sync(self):
        """Syncs UI after a short delay to ensure overlay is ready."""
        time.sleep(1)
        self.overlay.set_language_indicator(self.language)
        self.overlay.color_dropdown.set(self.current_color)
        self.overlay._on_color_change(self.current_color)

    def _on_clipboard_change(self, text: str):
        logger.debug(f"TRACER: Clipboard change received. Enabled: {self.clipboard_enabled}, Locked: {self.lock_manager.is_locked()}")
        if not self.clipboard_enabled:
            return
        
        # Broadened Interruption: If it's more than 20 chars, we treat it as a potential task
        # regardless of current lock state, ensuring the app stays responsive.
        if len(text.strip()) < 20 and self.lock_manager.is_locked():
            # Specifically check for short questions
            is_question = "?" in text or any(k in text.lower() for k in ["tell me", "solve", "explain", "how do I"])
            if not is_question:
                return
            
        self.trigger_copy_paste(text)

    def trigger_copy_paste(self, text: str = None):
        if not text:
            text = pyperclip.paste()
        logger.info(f"TRACER: Triggering Copy-Paste for text length: {len(text)}")
        self.audio_transcriber.pause()
        
        # COPY/PASTE now triggers ABSOLUTE_LOCK (BUNK mode).
        # This ensures the system stays locked and doesn't auto-unlock after generation.
        self.lock_manager.set_state(LockState.ABSOLUTE_LOCK)
        
        # Determine if it's raw data/problem statement
        import re
        data_pattern = r"(input|output|nums|target|arr|array)\s*="
        if re.search(data_pattern, text.lower()):
            prompt = f"Data pattern detected:\n\n{text}\n\nTask: Provide ONLY the {self.language} implementation to solve this. Strictly skip all theoretical explanations, introductions, or best-practice discussions. Code only."
        elif len(text.splitlines()) > 1:
            prompt = f"Problem statement detected:\n\n{text}\n\nTask: Provide a professional architectural explanation followed by the {self.language} implementation."
        else:
            prompt = text
            
        self.handle_question(prompt)

    def trigger_dsa_mode(self, text: str = None):
        if not text:
            text = pyperclip.paste()
        self.audio_transcriber.pause()
        # DSA now triggers ABSOLUTE_LOCK for consistency.
        self.lock_manager.set_state(LockState.ABSOLUTE_LOCK)
        prompt = f"DSA coding problem. Language: {self.language}. Provide professional explanation and implementation. \n\nProblem: {text}"
        self.handle_question(prompt, mode="DSA")

    def handle_question(self, question: str, mode="TECH"):
        logger.info(f"Processing {mode} request: {question[:50]}...")
        self.ui_queue.put("Thinking...")
        threading.Thread(target=self._ask_llm, args=(question, mode)).start()

    def _ask_llm(self, question: str, mode="TECH"):
        try:
            with open("system_prompt.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except:
            system_prompt = "You are a professional software engineer."

        if mode == "DSA":
            system_prompt = f"You are a software engineer in an interview solving a DSA problem. Speak in the first person ('I'). Explain your logical approach and time/space complexity naturally, then provide a clean {self.language} implementation."
        else:
            system_prompt += f"\n\nPRIMARY TARGET LANGUAGE: {self.language}. Provide all code examples, syntax, and solutions in this language."

        # Include Resume Context if available
        if os.path.exists("resume.txt"):
            try:
                with open("resume.txt", "r", encoding="utf-8") as f:
                    resume_content = f.read()
                system_prompt += f"\n\nUSER CONTEXT (RESUME):\n{resume_content}"
            except Exception as e:
                logger.warning(f"Failed to read resume: {e}")

        try:
            answer = self.current_client.ask(question, system_prompt=system_prompt, history=self.history)
            
            # Update History
            self.history.append({"role": "user", "content": question})
            self.history.append({"role": "assistant", "content": answer})
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
            
            # Ensure final token
            if not answer.strip().endswith("[X]"):
                answer = answer.strip() + " [X]"
                
            # Update Answer History and Index
            entry = {"question": question, "answer": answer}
            self.answer_history.append(entry)
            self.history_index = len(self.answer_history) - 1
                
            # UI Update
            self.ui_queue.put(answer)
            
            # Log to File
            self._log_interview(question, answer)
            
        except Exception as e:
            logger.error(f"LLM Request Failed: {e}")
            self.ui_queue.put(f"Error: {e} [X]")
        finally:
            # STRICT MODE: No auto-unlock, no auto-resume.
            # Master Lock must be manually released via UI click.
            logger.info("Generation complete. System remains LOCKED as per Strict Lock policy.")

    def _log_interview(self, question: str, answer: str):
        """Saves the question and answer to a timestamped log file."""
        log_dir = "interview_logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(log_dir, f"qa_{timestamp}.txt")
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"--- Question ---\n{question}\n\n")
                f.write(f"--- Answer ---\n{answer}\n")
            logger.info(f"Saved interview log to {filename}")
        except Exception as e:
            logger.error(f"Failed to write interview log: {e}")

    def show_prev_answer(self):
        if not self.answer_history or self.history_index <= 0:
            return # Already at oldest or none exists
        self.history_index -= 1
        entry = self.answer_history[self.history_index]
        self.overlay.show(f"[History {self.history_index+1}/{len(self.answer_history)}]\nQ: {entry['question'][:50]}...\n\n{entry['answer']}", duration=0)
        logger.info(f"Navigated to history index {self.history_index}")

    def show_next_answer(self):
        if not self.answer_history or self.history_index >= len(self.answer_history) - 1:
            return # Already at newest or none exists
        self.history_index += 1
        entry = self.answer_history[self.history_index]
        prefix = f"[History {self.history_index+1}/{len(self.answer_history)}]\n" if self.history_index < len(self.answer_history)-1 else ""
        self.overlay.show(f"{prefix}Q: {entry['question'][:50]}...\n\n{entry['answer']}", duration=0)
        logger.info(f"Navigated to history index {self.history_index}")

    def toggle_listen(self):
        self.listening = not self.listening
        self.overlay.set_voice_state(self.listening)
        if self.listening:
            self.audio_transcriber.resume()
            self.overlay.show("Listening ON", duration=0)
        else:
            self.audio_transcriber.pause()
            self.overlay.show("Listening OFF", duration=0)

    def clear_context(self):
        """Resets history and UI."""
        self.history = []
        self.answer_history = []
        self.history_index = -1
        self.ui_queue.put("")
        self.lock_manager.try_unlock(force=True)
        self.overlay.show("Context Cleared (Force Unlocked)", duration=2)
        self.history = []
        self.ui_queue.put(("caption", "", True))
        self.overlay.show("Context Cleared 🗑️", 2)
        logger.info("Application history and UI cleared.")

    def _on_volume(self, level):
        self.ui_queue.put(("volume", level))

    def toggle_language(self):
        """Cyclical toggle via hotkey."""
        modes = ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript", "Auto", "Interview"]
        if self.language not in modes: self.language = "Python"
        idx = (modes.index(self.language) + 1) % len(modes)
        self.set_language(modes[idx])
        logger.info(f"Language toggled to: {self.language}")

    def toggle_llm_mode(self):
        """Toggles between Local (Ollama) and Online (OpenAI) clients."""
        try:
            self.is_online = not getattr(self, "is_online", False)
            if self.is_online:
                # Mock initialization of OpenAI if not exists
                if not hasattr(self, "openai_client"):
                    self.openai_client = OpenAIClient(
                        api_key=os.getenv("OPENAI_API_KEY"),
                        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                    )
                self.current_client = self.openai_client
                self.overlay.show("Switched to Online ☁️ (OpenAI)", duration=0)
            else:
                self.current_client = self.ollama_client
                self.overlay.show("Switched to Offline 🏠 (Ollama)", duration=0)
            
            self.overlay.set_mode_icon(self.is_online)
            self._save_config()
        except Exception as e:
            logger.error(f"Failed to toggle mode: {e}")
            self.overlay.show("Mode Switch Failed")

    def handle_caption_input(self, text: str):
        """Alias for tests and legacy compatibility."""
        t = text.lower()
        if "?" in t or any(k in t for k in ["tell me", "solve", "explain", "how do I"]):
            self.handle_question(text)

    def toggle_clipboard(self):
        self.clipboard_enabled = not self.clipboard_enabled
        status = "ON" if self.clipboard_enabled else "OFF"
        self.overlay.show(f"Clipboard Monitoring: {status}", duration=0)
        logger.info(f"Clipboard monitoring toggled to: {status}")

    def rescan_audio(self):
        logger.info("Manual Audio Rescan Triggered...")
        self.audio_transcriber.stop()
        self.audio_transcriber.start()
        self.overlay.show("Rescanning Audio...", duration=0)

    def emergency_stop(self):
        logger.warning("Emergency Stop: Terminating...")
        self.audio_transcriber.stop()
        self.hotkeys.stop()
        self.root.destroy()
        os._exit(0)

    def toggle_lock(self):
        """Toggles the absolute lock from the UI."""
        self.lock_manager.toggle_absolute()
        logger.info(f"Master Lock toggled. Now: {self.lock_manager.get_state().name}")

    def copy_to_clipboard(self):
        """Copies current AI results to clipboard."""
        # Get content from overlay text area
        text = self.overlay.text_area.get("1.0", tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.overlay.show("Answer Copied! 📋", duration=2)
            logger.info("AI Result copied to clipboard.")
        else:
            self.overlay.show("Nothing to copy!", duration=2)

    def set_language(self, lang: str):
        """Sets the language explicitly (e.g., via dropdown)."""
        self.language = lang
        self.overlay.set_language_indicator(self.language)
        self.overlay.show(f"Language: {self.language}", duration=0) # Manual = Stay visible
        self._save_config()

    def set_color(self, color_name: str):
        """Sets the theme color and persists it."""
        self.current_color = color_name
        self._save_config()
        logger.info(f"Color persisted: {color_name}")

    def process_ui_queue(self):
        while not self.ui_queue.empty():
            item = self.ui_queue.get()
            if isinstance(item, tuple) and item[0] == "caption":
                _, text, is_final = item
                self.overlay.update_caption(text, is_final)
            elif isinstance(item, tuple) and item[0] == "volume":
                self.overlay.update_meter(item[1])
            else:
                # Forced display for AI answers/thinking status
                self.overlay.update_text(item, force=True)
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
