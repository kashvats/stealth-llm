
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock imports
sys.modules['tkinter'] = MagicMock()
sys.modules['stealth_overlay_modern'] = MagicMock()
sys.modules['clipboard_monitor'] = MagicMock()
sys.modules['scraper'] = MagicMock()
sys.modules['faster_whisper'] = MagicMock()
sys.modules['pyaudio'] = MagicMock()
sys.modules['audio_transcriber'] = MagicMock()

# Create proper mock classes for isinstance checks
class MockLLMClient: pass
class OpenAIClient: 
    def __init__(self, api_key=None): self.api_key = api_key
    def verify(self): return True
    def ask(self, q, system_prompt=None): return "OpenAI Answer"
class OllamaClient: 
    def __init__(self, model=None): self.model = model
    def verify(self): return True
    def ask(self, q, system_prompt=None): return "Ollama Answer"

# Assign to sys.modules
mock_llm = MagicMock()
mock_llm.MockLLMClient = MockLLMClient
mock_llm.OpenAIClient = OpenAIClient
mock_llm.OllamaClient = OllamaClient
# We also need get_client to return something if called, but main.py imports classes directly now.
# However, main imports get_client too.
mock_llm.get_client = MagicMock()

sys.modules['llm_client'] = mock_llm

from main import StealthPilotApp

class TestToggle(unittest.TestCase):
    def setUp(self):
        self.app = StealthPilotApp()
        # Manually set clients
        self.app.ollama_client = MagicMock()
        self.app.ollama_client.verify.return_value = True
        self.app.openai_client = MagicMock() # Mock object but acts as OpenAIClient
        self.app.openai_client.verify.return_value = True
        
        self.app.current_client = self.app.ollama_client
        self.app.is_online = False

    def test_toggle_offline_to_online(self):
        # Initial State
        self.assertFalse(self.app.is_online)
        self.assertEqual(self.app.current_client, self.app.ollama_client)
        
        # Action: Toggle
        self.app.toggle_llm_mode()
        
        # Assert State
        self.assertTrue(self.app.is_online)
        self.assertEqual(self.app.current_client, self.app.openai_client)
        
        # Verify Overlay Update
        self.app.overlay.show.assert_called_with("Switched to Online ☁️ (OpenAI)")
        self.app.overlay.set_mode_icon.assert_called_with(True)

    def test_toggle_online_to_offline(self):
        # Set to online first
        self.app.is_online = True
        self.app.current_client = self.app.openai_client
        
        # Action: Toggle
        self.app.toggle_llm_mode()
        
        # Assert State
        self.assertFalse(self.app.is_online)
        self.assertEqual(self.app.current_client, self.app.ollama_client)
        
        # Verify Overlay Update
        self.app.overlay.show.assert_called_with("Switched to Offline 🏠 (Ollama)")
        self.app.overlay.set_mode_icon.assert_called_with(False)

if __name__ == '__main__':
    unittest.main()
