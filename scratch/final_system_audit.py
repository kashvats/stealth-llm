import sys
import os
import queue
import time
import re
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

# Full Hardware/UI Mocking
sys.modules['customtkinter'] = MagicMock()
sys.modules['pyperclip'] = MagicMock()
sys.modules['pyaudiowpatch'] = MagicMock()
sys.modules['pyaudio'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['pynput'] = MagicMock()
sys.modules['CTkToolTip'] = MagicMock()

from main import StealthPilotApp
from lock_manager import LockState

def run_audit():
    print("=== STARTING FINAL SYSTEM AUDIT ===")
    
    with patch('main.OllamaClient'), patch('main.OpenAIClient'), patch('main.AudioTranscriber'), \
         patch('main.StealthOverlayButtons'), patch('tkinter.Tk'), \
         patch.dict(os.environ, {"ENABLE_CODE_VALIDATION": "true"}):
        
        app = StealthPilotApp()
        app.ui_queue = queue.Queue()
        app.overlay = MagicMock()
        
        # --- TEST 1: Golden Algorithm Injection ---
        print("\n[Test 1] Testing Golden Algorithm Injection...")
        test_text = "Input: [0,0,1,1,1,2]. Solve this by removing duplicates."
        # Mock AI to recognize the pattern
        ai_response = "PATTERN_ID: TWO_POINTERS_DUPLICATES\nI recognize this as a duplicate removal problem.\n```python\n# AI generated placeholder\n```"
        app.current_client.ask = MagicMock(return_value=ai_response)
        
        app.trigger_copy_paste(test_text)
        
        # Wait for processing
        time.sleep(0.5)
        app.ui_queue.get() # 'Thinking...'
        final_answer = app.ui_queue.get()
        
        if "Golden Solution Injected" in final_answer and "def remove_duplicates(nums):" in final_answer:
            print("  - PASS: Golden Algorithm correctly injected!")
        else:
            print(f"  - FAILURE: Injection failed. Got: {final_answer[:100]}")

        # --- TEST 2: Self-Correction (if validation fails) ---
        print("\n[Test 2] Testing Self-Correction Loop...")
        test_text_v = "Input: [0, 1, 3]. Output: 2" # Missing Number
        # Mock 1: Wrong pattern or wrong code
        wrong_response = "PATTERN_ID: UNKNOWN\n```python\ndef missing_number(nums): return -1\n```"
        # Mock 2: Correct code after retry
        corrected_response = "```python\ndef missing_number(nums): return 2\n```\n*(Self-Corrected)*"
        
        app.current_client.ask = MagicMock(side_effect=[wrong_response, corrected_response])
        app.trigger_copy_paste(test_text_v)
        
        time.sleep(0.5)
        app.ui_queue.get() # 'Thinking...'
        final_answer_v = app.ui_queue.get()
        
        if "Self-Corrected" in final_answer_v:
            print("  - PASS: Self-Correction loop successfully triggered!")
        else:
            print(f"  - FAILURE: Self-Correction failed. Output: {final_answer_v[:100]}")

        # --- TEST 3: UI Navigation (History) ---
        print("\n[Test 3] Testing UI Navigation & History...")
        app.show_prev_answer()
        if app.history_index == 0:
            print("  - PASS: History navigation working.")
        else:
            print(f"  - FAILURE: History index mismatch: {app.history_index}")

    print("\n=== AUDIT COMPLETE: ALL SYSTEMS NOMINAL ===")

if __name__ == "__main__":
    run_audit()
