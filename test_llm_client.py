import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_client import OpenAIClient, OllamaClient, MockLLMClient, get_client


class TestOpenAIClient:
    """Tests for OpenAI client implementation."""

    @pytest.fixture
    def client(self):
        return OpenAIClient(api_key="test-key-123", model="gpt-4o-mini")

    @patch("llm_client.requests.post")
    def test_ask_success(self, mock_post, client):
        """Test successful OpenAI API call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        result = client.ask("What is 2+2?", system_prompt="You are helpful")

        assert result == "Test response"
        mock_post.assert_called_once()

    @patch("llm_client.requests.post")
    def test_ask_with_history(self, mock_post, client):
        """Test OpenAI call with conversation history."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Follow-up response"}}]
        }
        mock_post.return_value = mock_response

        history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"}
        ]

        result = client.ask("Follow-up?", history=history)

        assert result == "Follow-up response"
        call_args = mock_post.call_args
        assert "messages" in call_args[1]["json"]

    @patch("llm_client.requests.post")
    def test_ask_api_error(self, mock_post, client):
        """Test handling of OpenAI API errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        result = client.ask("Test")

        assert "Error" in result
        assert "401" in result

    @patch("llm_client.requests.post")
    def test_ask_network_error(self, mock_post, client):
        """Test handling of network errors."""
        mock_post.side_effect = Exception("Connection failed")

        result = client.ask("Test")

        assert "Error" in result
        assert "Connection" in result

    @patch("llm_client.requests.post")
    def test_verify_success(self, mock_post, client):
        """Test successful verification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = client.verify()

        assert result is True

    @patch("llm_client.requests.post")
    def test_verify_failure(self, mock_post, client):
        """Test verification failure."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response

        result = client.verify()

        assert result is False


class TestOllamaClient:
    """Tests for Ollama local client."""

    @pytest.fixture
    def client(self):
        return OllamaClient(model="llama3.2")

    @patch("llm_client.os.getenv")
    @patch("llm_client.requests.post")
    def test_ask_success(self, mock_post, mock_env, client):
        """Test successful Ollama API call."""
        mock_env.return_value = "http://localhost:11434"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Ollama response"}
        }
        mock_post.return_value = mock_response

        result = client.ask("Hello")

        assert result == "Ollama response"

    @patch("llm_client.os.getenv")
    @patch("llm_client.requests.post")
    def test_ask_with_system_prompt(self, mock_post, mock_env, client):
        """Test Ollama call with system prompt."""
        mock_env.return_value = "http://localhost:11434"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"content": "Response"}
        }
        mock_post.return_value = mock_response

        result = client.ask("Test", system_prompt="You are an expert")

        assert result == "Response"
        call_args = mock_post.call_args
        messages = call_args[1]["json"]["messages"]
        assert messages[0]["role"] == "system"

    @patch("llm_client.os.getenv")
    @patch("llm_client.requests.post")
    def test_ask_api_error(self, mock_post, mock_env, client):
        """Test Ollama API error handling."""
        mock_env.return_value = "http://localhost:11434"

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Model not found"}
        mock_response.text = "Error"
        mock_post.return_value = mock_response

        result = client.ask("Test")

        assert "Error" in result

    @patch("llm_client.os.getenv")
    @patch("llm_client.requests.post")
    def test_ask_connection_error(self, mock_post, mock_env, client):
        """Test Ollama connection failure."""
        mock_env.return_value = "http://localhost:11434"
        mock_post.side_effect = Exception("Connection refused")

        result = client.ask("Test")

        assert "Error" in result

    @patch("llm_client.os.getenv")
    @patch("llm_client.requests.get")
    def test_verify_success(self, mock_get, mock_env, client):
        """Test successful Ollama verification."""
        mock_env.return_value = "http://localhost:11434"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = client.verify()

        assert result is True

    @patch("llm_client.os.getenv")
    @patch("llm_client.requests.get")
    def test_verify_failure(self, mock_get, mock_env, client):
        """Test Ollama verification failure."""
        mock_env.return_value = "http://localhost:11434"

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not found")
        mock_get.return_value = mock_response

        result = client.verify()

        assert result is False

    @patch("llm_client.os.getenv")
    @patch("llm_client.requests.post")
    def test_ask_keeps_model_alive(self, mock_post, mock_env, client):
        """Test that Ollama request includes keep_alive."""
        mock_env.return_value = "http://localhost:11434"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "OK"}}
        mock_post.return_value = mock_response

        client.ask("Test")

        call_args = mock_post.call_args
        assert call_args[1]["json"]["keep_alive"] == -1


class TestMockLLMClient:
    """Tests for mock client (testing fallback)."""

    def test_mock_response(self):
        """Test that mock client always returns a response."""
        client = MockLLMClient()

        result = client.ask("Any question")

        assert "Mock Answer" in result

    def test_mock_with_system_prompt(self):
        """Test mock respects system prompt parameter."""
        client = MockLLMClient()

        result = client.ask("Question", system_prompt="System context")

        assert "Mock Answer" in result

    def test_mock_with_history(self):
        """Test mock respects history parameter."""
        client = MockLLMClient()
        history = [{"role": "user", "content": "Previous"}]

        result = client.ask("Question", history=history)

        assert "Mock Answer" in result


class TestGetClientFactory:
    """Tests for get_client factory function."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("llm_client.OpenAIClient.verify")
    def test_get_client_openai_explicit(self, mock_verify):
        """Test explicit OpenAI provider selection."""
        mock_verify.return_value = True

        client = get_client(provider="openai", api_key="test-key")

        assert isinstance(client, OpenAIClient)

    @patch.dict("os.environ", {})
    @patch("llm_client.OllamaClient.verify")
    def test_get_client_ollama_explicit(self, mock_verify):
        """Test explicit Ollama provider selection."""
        mock_verify.return_value = True

        client = get_client(provider="ollama")

        assert isinstance(client, OllamaClient)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("llm_client.OpenAIClient.verify")
    def test_get_client_auto_detect_openai(self, mock_verify):
        """Test auto-detection of OpenAI via env var."""
        mock_verify.return_value = True

        client = get_client()

        assert isinstance(client, OpenAIClient)

    @patch.dict("os.environ", {})
    @patch("llm_client.OllamaClient.verify")
    def test_get_client_auto_detect_ollama(self, mock_verify):
        """Test auto-detection fallback to Ollama."""
        mock_verify.return_value = True

        client = get_client()

        assert isinstance(client, OllamaClient)

    @patch.dict("os.environ", {})
    @patch("llm_client.OpenAIClient.verify")
    @patch("llm_client.OllamaClient.verify")
    def test_get_client_all_fail_fallback_to_mock(self, mock_ollama_verify, mock_openai_verify):
        """Test fallback to MockLLMClient when all providers fail."""
        mock_openai_verify.return_value = False
        mock_ollama_verify.return_value = False

        client = get_client()

        assert isinstance(client, MockLLMClient)


class TestClientErrorHandling:
    """Tests for error handling across all clients."""

    @patch("llm_client.requests.post")
    def test_openai_json_parse_error(self, mock_post):
        """Test handling of malformed JSON from OpenAI."""
        client = OpenAIClient(api_key="test-key")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        result = client.ask("Test")

        assert "Error" in result

    @patch("llm_client.os.getenv")
    @patch("llm_client.requests.post")
    def test_ollama_malformed_response(self, mock_post, mock_env):
        """Test handling of unexpected Ollama response format."""
        mock_env.return_value = "http://localhost:11434"

        client = OllamaClient()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "format"}
        mock_post.return_value = mock_response

        result = client.ask("Test")

        assert "Error" in result or "KeyError" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
