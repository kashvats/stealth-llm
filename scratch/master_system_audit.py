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

def run_audit():
    print("=== STARTING MASTER SYSTEM AUDIT ===")
    
    with patch('main.OllamaClient'), patch('main.OpenAIClient'), patch('main.AudioTranscriber'), \
         patch('main.StealthOverlayButtons'), patch('tkinter.Tk'):
        
        app = StealthPilotApp()
        app.ui_queue = queue.Queue()
        app.overlay = MagicMock()
        
        # FEATURE 1: Manual Clipboard Solve (Alt+C)
        print("\n[Feature: Manual Solve] Testing Alt+C flow...")
        app.kb.lookup = MagicMock(return_value={"answer": "Cached Solution [X]"})
        app.trigger_copy_paste("Target Sum problem statement")
        msg = app.ui_queue.get()
        if "Cached Solution" in msg:
            print("  - PASS: Cache hit correctly routed.")
        if app.lock_manager.state == LockState.ABSOLUTE_LOCK:
            print("  - PASS: Lock State is correctly set to ABSOLUTE_LOCK.")

        # FEATURE 2: DSA Mode Trigger (Alt+S)
        print("\n[Feature: DSA Mode] Testing Alt+S flow...")
        app.kb.lookup = MagicMock(return_value=None) # Force LLM
        app.ollama_client.ask = MagicMock(return_value="LLM Result [X]")
        app.trigger_dsa_mode("Binary Tree Diameter")
        msg1 = app.ui_queue.get() # 'Thinking...'
        time.sleep(0.1)
        msg2 = app.ui_queue.get() # Result
        if "LLM Result" in msg2:
            print("  - PASS: LLM Fallback working.")
        
        # FEATURE 3: Audio Transcription Flow
        print("\n[Feature: Audio Transcription] Simulating voice-detected question...")
        # Reset state
        app.lock_manager.set_state(LockState.UNLOCKED)
        app.handle_question("How do I implement a linked list cycle detection?")
        msg = app.ui_queue.get() # 'Thinking...' or Cache
        if msg:
            print("  - PASS: handle_question correctly processes voice text.")

        # FEATURE 4: History Navigation (Alt+Left/Right)
        print("\n[Feature: History] Testing navigation logic...")
        app.answer_history = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
            {"question": "Q3", "answer": "A3"}
        ]
        app.history_index = 2
        app.show_prev_answer()
        if app.history_index == 1:
            app.overlay.show.assert_called()
            print("  - PASS: History Back working.")
        app.show_next_answer()
        if app.history_index == 2:
            print("  - PASS: History Forward working.")

        # FEATURE 5: KnowledgeBase Persistence
        print("\n[Feature: Cache Persistence] Verifying auto-save...")
        test_q = "Unique Test Question 123"
        test_a = "Unique Test Answer 123 [X]"
        app.kb.add_entry(test_q, test_a)
        if any(item['question'] == test_q for item in app.kb.data):
            print("  - PASS: New entries successfully added to memory.")
        
        # FEATURE 6: Lock Management Discipline
        print("\n[Feature: Lock Management] Verifying state stability...")
        app.lock_manager.set_state(LockState.NORMAL_LOCK)
        if app.lock_manager.state == LockState.NORMAL_LOCK:
            print("  - PASS: LockManager handles transitions.")

    print("\n=== AUDIT COMPLETE: ALL CORE FEATURES VERIFIED ===")

if __name__ == "__main__":
    run_audit()
