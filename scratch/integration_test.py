import sys
import os
import queue
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

# Mock the modules that require a display or hardware
sys.modules['customtkinter'] = MagicMock()
sys.modules['pyperclip'] = MagicMock()
sys.modules['pyaudiowpatch'] = MagicMock()
sys.modules['pyaudio'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['pynput'] = MagicMock()

from main import StealthPilotApp
from lock_manager import LockState

def test_system():
    print("Starting System Integration Test...")
    
    # Initialize app with mocked components
    with patch('main.OllamaClient'), patch('main.OpenAIClient'), patch('main.AudioTranscriber'), \
         patch('main.StealthOverlayButtons'), patch('tkinter.Tk'):
        app = StealthPilotApp()
        app.ui_queue = queue.Queue() 
        app.overlay = MagicMock() 
        app.lock_manager = MagicMock()
        
        # Test Case 1: Local Lookup (Two Sum)
        print("\n[Test 1] Simulating Copy-Paste of 'Two Sum'...")
        test_text = "Two Sum: Given an array of integers nums and an integer target, return indices..."
        app.trigger_copy_paste(test_text)
        
        result = app.ui_queue.get(timeout=2)
        if "⚡ [LOCAL MATCH FOUND]" in result:
            print("SUCCESS: Local match detected and routed to UI!")
        else:
            print(f"FAILURE: Expected local match, got: {result[:50]}")

        # Test Case 2: New Question (LLM Fallback + Cache)
        print("\n[Test 2] Simulating New Question (LLM Fallback)...")
        new_q = "Explain the difference between a Process and a Thread."
        
        # Mock LLM response
        app.ollama_client.ask = MagicMock(return_value="A process is an execution of a program...")
        
        # Trigger (This will spawn a thread, so we wait)
        app.trigger_copy_paste(new_q)
        
        # Check UI Queue (Should have 'Thinking...' then the answer)
        msg1 = app.ui_queue.get(timeout=2)
        print(f"UI Status: {msg1}")
        
        # Wait for LLM response in queue
        import time
        time.sleep(1) # Give thread time to finish
        msg2 = app.ui_queue.get(timeout=2)
        if "A process is an execution" in msg2:
            print("SUCCESS: LLM Fallback working!")
        
        # Check if it was cached
        match = app.kb.lookup(new_q)
        if match:
            print("SUCCESS: New question automatically cached to dsa.json!")
        else:
            print("FAILURE: Question was not cached.")

if __name__ == "__main__":
    test_system()
