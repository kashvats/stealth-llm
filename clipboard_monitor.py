import time
import pyperclip
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class ClipboardMonitor:
    def __init__(self, callback: Callable[[str], None], interval: float = 0.5):
        self.callback = callback
        self.interval = interval
        self.last_text = ""
        self.running = False

    def start(self):
        self.running = True
        self.last_text = pyperclip.paste()
        while self.running:
            try:
                current_text = pyperclip.paste()
                if current_text != self.last_text:
                    self.last_text = current_text
                    if self.is_question(current_text):
                        logger.info(f"Clipboard question detected: {current_text[:30]}...")
                        self.callback(current_text)
            except Exception as e:
                logger.error(f"Clipboard Error: {e}")
            time.sleep(self.interval)

    def stop(self):
        self.running = False

    def is_question(self, text: str) -> bool:
        if not text or len(text) > 400: # Ignore very long copies
            return False
            
        text = text.strip().lower()
        if "?" in text:
            return True
        
        keywords = ["what", "how", "why", "when", "who", "define", "explain"]
        if any(text.startswith(k) for k in keywords):
            return True
            
        return False
