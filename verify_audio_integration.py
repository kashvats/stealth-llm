
import unittest
from unittest.mock import MagicMock, patch
import queue
import sys

# Mock imports
sys.modules['tkinter'] = MagicMock()
sys.modules['overlay'] = MagicMock()
sys.modules['clipboard_monitor'] = MagicMock()
sys.modules['scraper'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['pyaudio'] = MagicMock()
# sys.modules['audio_transcriber'] = MagicMock() # We want to test integration with real class structure if possible, but mocking is safer for pure logic

from main import StealthPilotApp

class TestAudioIntegration(unittest.TestCase):
    def setUp(self):
        # Patch AudioTranscriber in main to avoid starting real threads
        with patch('main.AudioTranscriber') as MockAudioTranscriber:
            self.app = StealthPilotApp()
            self.mock_transcriber = MockAudioTranscriber.return_value
            # Manually capture the callbacks passed to __init__
            args, kwargs = MockAudioTranscriber.call_args
            self.on_partial = kwargs.get('on_partial')
            self.on_final = kwargs.get('on_final')

    def test_partial_callback(self):
        # Simulate partial callback
        self.on_partial("partial text")
        
        # Check queue
        item = self.app.ui_queue.get()
        self.assertEqual(item, ("caption", "partial text", False))

    def test_final_callback(self):
        # Mock handle_caption_input
        self.app.handle_caption_input = MagicMock()
        
        # Simulate final callback
        self.on_final("final text")
        
        # Check queue
        item = self.app.ui_queue.get()
        self.assertEqual(item, ("caption", "final text", True))
        
        # Check trigger logic called
        self.app.handle_caption_input.assert_called_with("final text")

    def test_process_ui_queue(self):
        # Mock overlay
        self.app.overlay = MagicMock()
        self.app.root = MagicMock() # mock after
        
        # Add items
        self.app.ui_queue.put(("caption", "partial", False))
        self.app.ui_queue.put(("caption", "final", True))
        self.app.ui_queue.put("regular text")
        
        # Run process_ui_queue once
        # logic: while loop until empty.
        
        self.app.process_ui_queue()
        
        # Verify calls
        pass
        # assert calls in order
        calls = self.app.overlay.method_calls
        # This is tricky because method_calls might gather arbitrary calls.
        # Let's check update_caption calls
        self.app.overlay.update_caption.assert_any_call("partial", False)
        self.app.overlay.update_caption.assert_any_call("final", True)
        self.app.overlay.update_text.assert_any_call("regular text")

if __name__ == '__main__':
    unittest.main()
