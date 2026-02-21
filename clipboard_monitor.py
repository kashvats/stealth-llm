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

    def start(self):
        self.running = True
        self.last_text = pyperclip.paste()
        while self.running:
            try:
                current_text = pyperclip.paste()
                if current_text != self.last_text:
                    logger.debug(f"Clipboard changed detected. Length: {len(current_text)}")
                    self.last_text = current_text
                    if self.is_question(current_text):
                        logger.info(f"Clipboard question accepted: {current_text[:30]}...")
                        self.callback(current_text)
                    else:
                        logger.debug("Clipboard change ignored by is_question filter.")
            except Exception as e:
                logger.error(f"Clipboard Error: {e}")
            time.sleep(self.interval)

    def stop(self):
        self.running = False

    def is_question(self, text: str) -> bool:
        if not text: return False
        text_clean = text.strip()
        if len(text_clean) < 2: return False # Allow very short snippets like 'a=1'
        if len(text_clean) > 5000: return False 
            
        t_lower = text_clean.lower()
        # Direct questions
        if "?" in t_lower: return True
        
        # Coding keywords (using regex for input/output patterns)
        coding_keys = ["def ", "class ", "import ", "solve", "implement", "function"]
        if any(k in t_lower for k in coding_keys): return True
        
        # Regex for data patterns like input=[...] or nums = [...] or just arr = [...]
        # Also detect raw bracket patterns that look like data
        data_pattern = r"(input|output|nums|target|arr|array|list|data)\s*=|\[.*\]"
        if re.search(data_pattern, t_lower): return True
            
        # Question starters
        q_starters = ["what", "how", "why", "when", "who", "define", "explain"]
        if any(t_lower.startswith(k) for k in q_starters): return True
            
        # Multi-line usually means a problem statement or code
        if len(text_clean.splitlines()) >= 2: return True
            
        return False
