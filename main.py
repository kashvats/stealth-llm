import threading
import asyncio
import logging
import tkinter as tk
from queue import Queue
import os

from overlay import StealthOverlay
from clipboard_monitor import ClipboardMonitor
from scraper import CaptionScraper
from llm_client import get_client, MockLLMClient, OpenAIClient, OllamaClient
from audio_transcriber import AudioTranscriber
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StealthPilotApp:
    def __init__(self):
        self.root = tk.Tk()
        
        # Load Config
        local_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize Clients
        self.ollama_client = OllamaClient(model=local_model)
        if api_key:
            self.openai_client = OpenAIClient(api_key=api_key)
        else:
            self.openai_client = MockLLMClient() # Placeholder if no key
            
        self.is_online = False # Default to Offline
        self.current_client = self.ollama_client
        
        # Verify default
        if not self.current_client.verify():
             # Try fallback to OpenAI if Ollama fails? Or just warn?
             logger.warning("Default Ollama client failed verification.")
        
        self.overlay = StealthOverlay(self.root, on_toggle_mode=self.toggle_llm_mode)
        self.overlay.set_mode_icon(self.is_online)
        
        # Check if we fell back to Mock (if using OpenAI as default, but we aren't)
        # Just generic check
        if isinstance(self.current_client, MockLLMClient):
            self.root.after(1000, lambda: self.overlay.show("⚠️ LLM Connection Failed using Mock", 5))
        
        self.clipboard_monitor = ClipboardMonitor(callback=self.handle_question)
        self.scraper = CaptionScraper()
        self.ui_queue = Queue()
        
        # Initialize Audio Transcriber
        self.audio_transcriber = AudioTranscriber(
            on_partial=lambda text: self.ui_queue.put(("caption", text, False)),
            on_final=self._handle_final_speech
        )

    def toggle_llm_mode(self):
        if self.is_online:
            # Switch to Offline
            self.current_client = self.ollama_client
            self.is_online = False
            self.overlay.show("Switched to Offline 🏠 (Ollama)")
        else:
            # Switch to Online
            if isinstance(self.openai_client, MockLLMClient):
                 self.overlay.show("⚠️ No OpenAI Key found!", 3)
                 return
            
            self.current_client = self.openai_client
            self.is_online = True
            self.overlay.show("Switched to Online ☁️ (OpenAI)")
            
        self.overlay.set_mode_icon(self.is_online)

    def _handle_final_speech(self, text: str):
        self.ui_queue.put(("caption", text, True))
        self.handle_caption_input(text)

    def handle_question(self, question: str):
        logger.info(f"Processing question: {question}")
        self.ui_queue.put("Thinking...")
        
        # Run LLM call in a separate thread to not block UI or Clipboard
        threading.Thread(target=self._ask_llm, args=(question,)).start()

    def _ask_llm(self, question: str):
        # Load System Prompt
        try:
            with open("system_prompt.txt", "r", encoding="utf-8") as f:
                system_prompt = f.read()
            
            # Append Resume Context if available
            if os.path.exists("resume_text.txt"):
                with open("resume_text.txt", "r", encoding="utf-8") as f:
                    resume_text = f.read()
                system_prompt += f"\n\nUSER CONTEXT (RESUME):\n{resume_text}\n"
                system_prompt += "\nINSTRUCTION: YOU are the person described in the resume. When asked to introduce yourself, use this context. Speak naturally as if you are this person."
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            system_prompt = "You are a helpful stealth assistant. concise answers."

        answer = self.current_client.ask(question, system_prompt=system_prompt)
        self.ui_queue.put(f"Q: {question}\n\nA: {answer}")

    def process_ui_queue(self):
        while not self.ui_queue.empty():
            item = self.ui_queue.get()
            if isinstance(item, tuple) and item[0] == "caption":
                _, text, is_final = item
                self.overlay.update_caption(text, is_final)
            else:
                self.overlay.update_text(item)
        self.root.after(100, self.process_ui_queue)

    def start_scraper_thread(self):
        def run_async_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Pass a callback to the scraper
            self.scraper.on_caption = self.handle_caption_input
            loop.run_until_complete(self.scraper.connect())
        
        # Scraper thread
        t = threading.Thread(target=run_async_loop, daemon=True)
        t.start()

    def handle_caption_input(self, text: str):
        # Heuristic: if text looks like a question, ask LLM
        # "tell me" is also a trigger
        text_lower = text.lower()
        if ("?" in text and len(text) > 10) or ("tell me" in text_lower and len(text) > 10):
             self.handle_question(text)

    def start_clipboard_thread(self):
        t = threading.Thread(target=self.clipboard_monitor.start, daemon=True)
        t.start()

    def run(self):
        self.start_clipboard_thread()
        self.start_scraper_thread() # Enabled
        self.audio_transcriber.start()
        
        self.root.after(100, self.process_ui_queue)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.clipboard_monitor.stop()
            self.scraper.stop()
            self.audio_transcriber.stop()

if __name__ == "__main__":
    app = StealthPilotApp()
    app.run()
