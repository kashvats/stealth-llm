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
import re

from stealth_overlay_buttons import StealthOverlayButtons
from clipboard_monitor import ClipboardMonitor
from llm_client import OllamaClient, OpenAIClient, MockLLMClient
from audio_transcriber import AudioTranscriber
from lock_manager import LockManager, LockState
from hotkey_listener import GlobalHotkeyListener
from knowledge_base import KnowledgeBase

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StealthPilotApp:
    def __init__(self):
        self.root = tk.Tk()
        
        # Lock Manager
        self.lock_manager = LockManager(on_state_change=self._handle_lock_change)
        
        # Knowledge Base (Local Cache)
        self.kb = KnowledgeBase("dsa.json")
        
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
        default_config = {
            "language": "Python",
            "color_theme": "Green",
            "llm_mode": "cloud"
        }

        try:
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    cfg = json.load(f)
                self.language = cfg.get("language", default_config["language"])
                self.current_color = cfg.get("color_theme", default_config["color_theme"])
                self.is_online = (cfg.get("llm_mode", default_config["llm_mode"]) == "cloud")
                logger.info(f"Config loaded from file: Lang={self.language}, Color={self.current_color}, Online={self.is_online}")
            else:
                logger.info("Config file not found, using defaults")
                self.language = default_config["language"]
                self.current_color = default_config["color_theme"]
                self.is_online = (default_config["llm_mode"] == "cloud")
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt config.json: {e}. Using defaults.")
            self.language = default_config["language"]
            self.current_color = default_config["color_theme"]
            self.is_online = (default_config["llm_mode"] == "cloud")
        except IOError as e:
            logger.error(f"Cannot read config.json: {e}. Using defaults.")
            self.language = default_config["language"]
            self.current_color = default_config["color_theme"]
            self.is_online = (default_config["llm_mode"] == "cloud")
        except Exception as e:
            logger.error(f"Unexpected error loading config: {type(e).__name__}: {e}. Using defaults.")
            self.language = default_config["language"]
            self.current_color = default_config["color_theme"]
            self.is_online = (default_config["llm_mode"] == "cloud")

        # Initialize OpenAI client if online mode
        if self.is_online and not hasattr(self, "openai_client"):
            try:
                self.openai_client = OpenAIClient(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                )
                self.current_client = self.openai_client
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}. Falling back to Ollama.")
                self.current_client = self.ollama_client

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
        if not self.clipboard_enabled:
            return
            
        text_clean = text.strip()
        if len(text_clean) < 5:
            return # Ignore tiny copies
            
        logger.info(f"Clipboard Seen: '{text_clean[:30]}...'")
        
        # Visual feedback: Detect copy
        logger.info(f"Clipboard Detection: {text_clean[:20]}...")
        
        is_locked = self.lock_manager.is_locked()
        
        # Smart Trigger Logic:
        # If UNLOCKED, solve everything.
        # If LOCKED, only solve if it looks like a real problem or question.
        should_process = not is_locked
        
        if is_locked:
            lower_text = text_clean.lower()
            # Technical problem signatures
            signatures = ["?", "nums", "target", "input:", "output:", "solve", "explain", "def ", "class ", "function"]
            if any(sig in lower_text for sig in signatures):
                should_process = True
            elif len(text_clean) > 300: # Very long text is likely a problem statement
                should_process = True

        if should_process:
            logger.info("Smart Trigger: Processing clipboard change.")
            self.trigger_copy_paste(text_clean)
        else:
            logger.info("Smart Trigger: Ignored trivial/random copy while LOCKED.")

    def trigger_copy_paste(self, text: str = None):
        if not text:
            text = pyperclip.paste()
        logger.info(f"TRACER: Triggering Copy-Paste for text length: {len(text)}")
        self.audio_transcriber.pause()
        self.lock_manager.set_state(LockState.ABSOLUTE_LOCK)

        # 1. Try Local Lookup on RAW text first
        local_result = self.kb.lookup(text)
        if local_result:
            answer = local_result.get("answer", "")
            if not answer.strip().endswith("[X]"):
                answer = answer.strip() + " [X]"
            header = "⚡ [LOCAL MATCH FOUND]\n\n"
            self.ui_queue.put(header + answer)
            logger.info("Matched raw text in local knowledge base.")
            return

        # 2. Pattern detection for mode selection
        import re
        code_pattern = r"(def\s+|class\s+|function|public\s+static|void|int\s+)"
        data_pattern = r"(input|output|nums|target|arr|array)\s*[=:]"
        
        is_code = re.search(code_pattern, text)
        has_data = re.search(data_pattern, text.lower())
        
        mode = "TECH"
        if is_code or has_data or len(text.splitlines()) > 5:
            mode = "DSA"
            prompt = f"Analyze this input and provide the correct DSA solution:\n\n{text}"
        else:
            prompt = text
            
        # 3. Extract Test Data for Validation
            
        # 3. Extract Test Data for Validation
        test_input = None
        expected_output = None
        input_match = re.search(r"(?:input|nums1?|target)\s*[=:]\s*([^\n\r]*)", text, re.I)
        output_match = re.search(r"output\s*[=:]\s*([^\n\r]*)", text, re.I)
        if input_match: test_input = input_match.group(1).strip()
        if output_match: expected_output = output_match.group(1).strip()
        
        if test_input: logger.info(f"Detected Test Input: {test_input}")
        if expected_output: logger.info(f"Detected Expected Output: {expected_output}")

        # 4. Proceed to LLM with augmented prompt
        self.ui_queue.put("Thinking...")
        threading.Thread(target=self._ask_llm, args=(prompt, "TECH", test_input, expected_output)).start()

    def trigger_dsa_mode(self, text: str = None):
        if not text:
            text = pyperclip.paste()
        self.audio_transcriber.pause()
        self.lock_manager.set_state(LockState.ABSOLUTE_LOCK)
        
        # 1. Try Local Lookup on RAW text first
        local_result = self.kb.lookup(text)
        if local_result:
            answer = local_result.get("answer", "")
            if not answer.strip().endswith("[X]"):
                answer = answer.strip() + " [X]"
            header = "⚡ [LOCAL DSA MATCH]\n\n"
            self.ui_queue.put(header + answer)
            return

        # 2. Proceed to LLM
        prompt = f"DSA coding problem. Language: {self.language}. Provide professional explanation and implementation. \n\nProblem: {text}"
        self.handle_question(prompt, mode="DSA")

    def handle_question(self, question: str, mode="TECH"):
        # This is now the 'LLM-only' or 'Legacy' entry point
        # KnowledgeBase lookup is now handled upstream in trigger methods for better context control
        logger.info(f"Processing {mode} LLM request: {question[:50]}...")
        self.ui_queue.put("Thinking...")
        threading.Thread(target=self._ask_llm, args=(question, mode, None, None)).start()

    def _ask_llm(self, question: str, mode: str = "TECH", test_input: str = None, expected_output: str = None):
        """Worker thread for LLM requests. Handles validation if enabled."""
        system_prompt = "You are 'The Silent Strategist', an elite AI assistant for technical interviews. "
        if mode == "DSA":
            # Inject Pattern IDs into system prompt for identification
            pattern_list = ", ".join([p["id"] for p in self.kb.patterns])
            system_prompt = (
                f"You are an elite software engineer. Analyze the provided input (text or code).\n"
                f"1. Determine the core DSA problem being solved.\n"
                f"2. If it matches a pattern in this list: [{pattern_list}], you MUST start your response with 'PATTERN_ID: <ID>'.\n"
                f"3. Then provide a professional, optimized {self.language} solution. Speak in the first person ('I')."
            )
        else:
            system_prompt += f"\n\nPRIMARY TARGET LANGUAGE: {self.language}. Provide all code examples, syntax, and solutions in this language."

        # Feature Flags
        do_validate = os.getenv("ENABLE_CODE_VALIDATION", "false").lower() == "true"
        from code_validator import CodeValidator
        
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
            
            # Pattern Injection Loop
            if "PATTERN_ID:" in answer:
                try:
                    p_id = answer.split("PATTERN_ID:")[1].split()[0].strip().replace(",", "").replace(".", "")
                    golden_algo = self.kb.get_pattern(p_id)
                    if golden_algo:
                        logger.info(f"Injecting Golden Solution for pattern: {p_id}")
                        # Replace the AI code block with Golden Code
                        golden_md = f"\n\n```python\n{golden_algo['code']}\n```\n*(Golden Solution Injected)*"
                        # Simple replacement of the code block part
                        answer = re.sub(r"```python\n.*?\n```", golden_md, answer, flags=re.DOTALL)
                except Exception as e:
                    logger.warning(f"Failed to inject golden solution: {e}")

            # Validation Loop
            if do_validate and test_input and expected_output:
                code = CodeValidator.extract_python_code(answer)
                if code:
                    logger.info(f"Validating code against input={test_input}, expected={expected_output}...")
                    success, feedback = CodeValidator.validate_logic(code, test_input, expected_output)
                    if not success:
                        logger.warning(f"Validation failed: {feedback}. Retrying LLM...")
                        retry_prompt = f"The previous code failed validation.\nError: {feedback}\n\nPlease fix the code and ensure it returns {expected_output} for input {test_input}."
                        answer = self.current_client.ask(retry_prompt, system_prompt=system_prompt, history=self.history)
                        answer += f"\n\n*(Self-Corrected after validation fail: {feedback})*"
                    else:
                        logger.info("Validation successful!")
                        answer += "\n\n*(Verified with internal test case)*"

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
            
            # Update Knowledge Base (Cache for next time)
            if "Error" not in answer and (mode == "DSA" or len(question) > 20):
                self.kb.add_entry(question, answer, category=mode)
            
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
        try:
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(log_dir, f"qa_{timestamp}.txt")

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"--- Question ---\n{question}\n\n")
                f.write(f"--- Answer ---\n{answer}\n")
            logger.info(f"Saved interview log to {filename}")
        except OSError as e:
            logger.error(f"Cannot write interview log (disk/permissions): {e}")
        except Exception as e:
            logger.error(f"Unexpected error writing interview log: {type(e).__name__}: {e}")

    def show_prev_answer(self):
        if not self.answer_history or self.history_index <= 0:
            return # Already at oldest or none exists
        self.history_index -= 1
        entry = self.answer_history[self.history_index]
        self.overlay.update_text(f"[History {self.history_index+1}/{len(self.answer_history)}]\nQ: {entry['question'][:50]}...\n\n{entry['answer']}", force=True)
        logger.info(f"Navigated to history index {self.history_index}")

    def show_next_answer(self):
        if not self.answer_history or self.history_index >= len(self.answer_history) - 1:
            return # Already at newest or none exists
        self.history_index += 1
        entry = self.answer_history[self.history_index]
        prefix = f"[History {self.history_index+1}/{len(self.answer_history)}]\n" if self.history_index < len(self.answer_history)-1 else ""
        self.overlay.update_text(f"{prefix}Q: {entry['question'][:50]}...\n\n{entry['answer']}", force=True)
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
