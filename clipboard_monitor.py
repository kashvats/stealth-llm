import time
import pyperclip
import logging
import re
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class ClipboardMonitor:
    def __init__(self, callback: Callable[[str], None], interval: float = 0.5):
        self.callback = callback
        self.interval = interval
        self.last_text = ""
        self.running = False

    def is_valid_text(self, text: str) -> bool:
        """Basic validation to ensure we have actual text content."""
        if not text:
            return False
        text_clean = text.strip()
        if len(text_clean) < 2:
            return False
        if len(text_clean) > 50000: # Sanity limit for huge copies
            return False
        return True

    def start(self):
        self.running = True
        self.last_text = pyperclip.paste()
        logger.info("Clipboard Monitor Started (Transparent Mode).")
        while self.running:
            try:
                current_text = pyperclip.paste()
                if current_text != self.last_text:
                    self.last_text = current_text
                    if self.is_valid_text(current_text):
                        logger.debug(f"Clipboard change detected (Length: {len(current_text)}). Emitting to app.")
                        self.callback(current_text)
            except Exception as e:
                logger.error(f"Clipboard Error: {e}")
            time.sleep(self.interval)
