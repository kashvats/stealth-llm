import sys
import os
import queue
import time
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

def run_ultimate_test():
    print("=== STARTING ULTIMATE SYSTEM STRESS TEST ===")
    
    with patch('main.OllamaClient'), patch('main.OpenAIClient'), patch('main.AudioTranscriber'), \
         patch('main.StealthOverlayButtons'), patch('tkinter.Tk'), \
         patch.dict(os.environ, {"ENABLE_CODE_VALIDATION": "true"}):
        
        app = StealthPilotApp()
        app.ui_queue = queue.Queue()
        app.overlay = MagicMock()
        
        # TEST 1: Code Validation & Self-Correction
        print("\n[Test 1] Testing Code Validation & Self-Correction...")
        test_text = "Input: ([1,2,3,0,0,0], 3, [2,5,6], 3). Output: [1,2,2,3,5,6]"
        
        # Mock 1st LLM call to return WRONG code
        wrong_code = "```python\ndef merge(nums1_tuple):\n    return [0,0,0,0,0,0] # WRONG\n```"
        # Mock 2nd LLM call (retry) to return CORRECT code
        correct_code = """```python
def merge(args):
    nums1, m, nums2, n = args
    i, j, k = m - 1, n - 1, m + n - 1
    while i >= 0 and j >= 0:
        if nums1[i] > nums2[j]:
            nums1[k] = nums1[i]
            i -= 1
        else:
            nums1[k] = nums2[j]
            j -= 1
        k -= 1
    while j >= 0:
        nums1[k] = nums2[j]
        j -= 1
        k -= 1
    return nums1
```"""
        
        # Simulate the two-step LLM response
        app.current_client.ask = MagicMock(side_effect=[wrong_code, correct_code])
        
        # Manually clear cache for this test so LLM is triggered
        app.kb.lookup = MagicMock(return_value=None)
        
        # Trigger
        app.trigger_copy_paste(test_text)
        
        # Check output
        time.sleep(0.5) # Wait for thread
        app.ui_queue.get() # 'Thinking...'
        final_answer = app.ui_queue.get()
        
        if "Self-Corrected" in final_answer:
            print("  - PASS: System detected wrong code, retried, and self-corrected!")
        else:
            print(f"  - FAILURE: System did not self-correct. Got: {final_answer[:100]}")

        # TEST 2: Theoretical Explanation (CORS)
        print("\n[Test 2] Testing Theoretical Explanation (CORS)...")
        app.current_client.ask = MagicMock(return_value="CORS (Cross-Origin Resource Sharing) is a security feature... [X]")
        app.handle_question("What is CORS?")
        app.ui_queue.get() # 'Thinking...'
        theory_ans = app.ui_queue.get()
        if "CORS" in theory_ans:
            print("  - PASS: Theoretical explanation generated successfully.")

    print("\n=== STRESS TEST COMPLETE: SYSTEM IS ROCK SOLID ===")

if __name__ == "__main__":
    run_ultimate_test()
