
import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Mock tkinter and others
sys.modules['tkinter'] = MagicMock()
sys.modules['stealth_overlay_modern'] = MagicMock()
sys.modules['clipboard_monitor'] = MagicMock()
sys.modules['scraper'] = MagicMock()

# Import the class to test
from main import StealthPilotApp

class TestComponents(unittest.TestCase):
    def setUp(self):
        self.app = StealthPilotApp()
        self.app.handle_question = MagicMock()

    def test_caption_triggers(self):
        # Test ? trigger
        self.app.handle_caption_input("What is the time?")
        self.app.handle_question.assert_called()
        
        self.app.handle_question.reset_mock()
        
        # Test "tell me" trigger
        self.app.handle_caption_input("Tell me about yourself")
        self.app.handle_question.assert_called()
        
        self.app.handle_question.reset_mock()
        
        # Test non-trigger
        self.app.handle_caption_input("Just a random sentence without the magic words.")
        self.app.handle_question.assert_not_called()

    @patch('main.threading.Thread')
    @patch('main.threading.Timer')
    @patch('builtins.open')
    @patch('os.path.exists')
    def test_ask_llm_prompts(self, mock_exists, mock_open, mock_timer, mock_thread):
        # Setup mock thread to run target immediately and synchronously
        mock_thread.side_effect = lambda target, args=(), kwargs={}: MagicMock(start=lambda: target(*args, **kwargs))
        mock_timer.side_effect = lambda interval, callback, args=(), kwargs={}: MagicMock(start=lambda: callback(*args, **kwargs))
        # Setup mocks for file reading
        mock_exists.return_value = True # resume triggers
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        # Reading system_prompt.txt then resume.txt
        mock_file.read.side_effect = ["Base System Prompt", "Resume Content"]
        
        self.app.current_client = MagicMock()
        self.app.ui_queue = MagicMock()
        
        # Call _ask_llm
        self.app._ask_llm("Intro?")
        
        # Verify LLM called with combined prompt
        call_args = self.app.current_client.ask.call_args
        self.assertIsNotNone(call_args)
        
        prompt_arg = call_args[1]['system_prompt']
        self.assertIn("Base System Prompt", prompt_arg)
        self.assertIn("Resume Content", prompt_arg)
        self.assertIn("USER CONTEXT (RESUME)", prompt_arg)

if __name__ == '__main__':
    unittest.main()
