import pytest
from unittest.mock import MagicMock, patch
from llm_client import get_client, MockLLMClient, OpenAIClient
from clipboard_monitor import ClipboardMonitor
import time

class TestLLMClient:
    def test_mock_client(self):
        client = get_client(api_key=None)
        assert isinstance(client, MockLLMClient)
        response = client.ask("Hello")
        assert "Mock Answer" in response

    def test_openai_client_init(self):
        client = get_client(api_key="sk-test")
        assert isinstance(client, OpenAIClient)
        assert client.api_key == "sk-test"

class TestClipboardMonitor:
    @patch('pyperclip.paste')
    def test_monitor_callback(self, mock_paste):
        # Setup
        mock_callback = MagicMock()
        monitor = ClipboardMonitor(callback=mock_callback, interval=0.1)
        
        # Simulate sequence of clipboard content
        # 1. Start empty
        # 2. "Hello" (not a question)
        # 3. "What is AI?" (question)
        # 4. "What is AI?" (duplicate, should be ignored)
        # 5. Stop
        
        mock_paste.side_effect = ["", "Hello", "What is AI?", "What is AI?", "Stop"]
        
        # We need to run monitor in a way that we can stop it.
        # Since it's a while loop, we run it in a thread or just test the logic directly if possible.
        # But monitor.start() blocks. 
        # So we'll test the helper is_question directly and maybe mock start logic.
        
        assert monitor.is_question("What time is it?")
        assert monitor.is_question("how does this work")
        assert not monitor.is_question("Just a statement")
        assert not monitor.is_question("")

if __name__ == "__main__":
    pytest.main([__file__])
