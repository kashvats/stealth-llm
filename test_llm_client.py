import pytest
from unittest.mock import Mock, patch, MagicMock
from llm_client import OpenAIClient, OllamaClient, MockLLMClient, LlamaCppClient, get_client


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

    @patch("llm_client.requests.post")
    def test_ask_keeps_model_alive(self, mock_post, client):
        """Test that Ollama request includes keep_alive from env (default 300)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "OK"}}
        mock_post.return_value = mock_response

        client.ask("Test")

        call_args = mock_post.call_args
        # keep_alive should be an int (env default 300 when not set)
        assert isinstance(call_args[1]["json"]["keep_alive"], int)


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

    @patch.dict("os.environ", {})
    @patch("llm_client.LlamaCppClient.verify")
    def test_get_client_llamacpp_explicit(self, mock_verify):
        """Test explicit llamacpp provider selection."""
        mock_verify.return_value = True

        client = get_client(provider="llamacpp")

        assert isinstance(client, LlamaCppClient)

    @patch.dict("os.environ", {})
    @patch("llm_client.LlamaCppClient.verify")
    def test_get_client_llama_cpp_alias(self, mock_verify):
        """Test llama.cpp alias in provider argument."""
        mock_verify.return_value = True

        client = get_client(provider="llama.cpp")

        assert isinstance(client, LlamaCppClient)

    @patch.dict("os.environ", {"LLM_PROVIDER": "llamacpp"})
    @patch("llm_client.LlamaCppClient.verify")
    def test_get_client_auto_detect_llamacpp_env(self, mock_verify):
        """Test auto-detection via LLM_PROVIDER=llamacpp."""
        mock_verify.return_value = True

        client = get_client()

        assert isinstance(client, LlamaCppClient)

    @patch.dict("os.environ", {"LLAMACPP_BASE_URL": "http://localhost:8080"})
    @patch("llm_client.LlamaCppClient.verify")
    def test_get_client_auto_detect_llamacpp_base_url(self, mock_verify):
        """Test auto-detection when LLAMACPP_BASE_URL is set in environment."""
        mock_verify.return_value = True

        client = get_client()

        assert isinstance(client, LlamaCppClient)

    @patch.dict("os.environ", {})
    @patch("llm_client.LlamaCppClient.verify")
    def test_get_client_llamacpp_failed_fallback_mock(self, mock_verify):
        """Test that failed llamacpp provider falls back to MockLLMClient."""
        mock_verify.return_value = False

        client = get_client(provider="llamacpp")

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

    @patch("llm_client.requests.post")
    def test_llamacpp_malformed_response(self, mock_post):
        """Test handling of unexpected llama.cpp response format."""
        client = LlamaCppClient()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected": "format"}
        mock_post.return_value = mock_response

        result = client.ask("Test")

        assert "Error" in result or "KeyError" in result


class TestLlamaCppClientServer:
    """Tests for llama.cpp client in HTTP server mode."""

    @pytest.fixture
    def client(self):
        return LlamaCppClient(base_url="http://localhost:8080")

    @patch("llm_client.requests.post")
    def test_ask_success(self, mock_post, client):
        """Test successful llama.cpp server call via /v1/chat/completions."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "llama response"}}]
        }
        mock_post.return_value = mock_response

        result = client.ask("Hello llama")

        assert result == "llama response"
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == "http://localhost:8080/v1/chat/completions"

    @patch("llm_client.requests.post")
    def test_ask_with_system_prompt_and_history(self, mock_post, client):
        """Test llama.cpp server call with system prompt and history."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Answer"}}]
        }
        mock_post.return_value = mock_response

        history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]
        result = client.ask("Follow-up", system_prompt="Be concise", history=history)

        assert result == "Answer"
        messages = mock_post.call_args[1]["json"]["messages"]
        assert messages[0] == {"role": "system", "content": "Be concise"}
        assert messages[1] == {"role": "user", "content": "Hi"}
        assert messages[2] == {"role": "assistant", "content": "Hello"}
        assert messages[3] == {"role": "user", "content": "Follow-up"}

    @patch("llm_client.requests.post")
    def test_ask_api_error(self, mock_post, client):
        """Test error handling when llama.cpp server returns non-200."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": {"message": "Server error"}}
        mock_response.text = "Server error"
        mock_post.return_value = mock_response

        result = client.ask("Test")

        assert "Error" in result

    @patch("llm_client.requests.post")
    def test_ask_network_error(self, mock_post, client):
        """Test network failure handling."""
        mock_post.side_effect = Exception("Connection refused")

        result = client.ask("Test")

        assert "Error" in result
        assert "Connection" in result

    @patch("llm_client.requests.post")
    def test_ask_stream_success(self, mock_post, client):
        """Test streaming from llama.cpp server."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        lines = [
            b'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            b'data: {"choices":[{"delta":{"content":" world"}}]}',
            b'data: [DONE]'
        ]
        mock_response.iter_lines.return_value = lines
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False
        mock_post.return_value = mock_response

        tokens = list(client.ask_stream("Hello"))

        assert tokens == ["Hello", " world"]

    @patch("llm_client.requests.post")
    def test_ask_stream_error(self, mock_post, client):
        """Test streaming error handling when status code != 200."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False
        mock_post.return_value = mock_response

        tokens = list(client.ask_stream("Hello"))

        assert len(tokens) == 1
        assert "Error" in tokens[0]

    @patch("llm_client.requests.get")
    def test_verify_health_success(self, mock_get, client):
        """Test verify succeeds when /health returns 200."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        assert client.verify() is True
        mock_get.assert_called_with("http://localhost:8080/health", headers={"Content-Type": "application/json"}, timeout=5)

    @patch("llm_client.requests.get")
    def test_verify_models_fallback_success(self, mock_get, client):
        """Test verify falls back to /v1/models if /health fails."""
        health_resp = Mock()
        health_resp.status_code = 404
        models_resp = Mock()
        models_resp.status_code = 200
        mock_get.side_effect = [health_resp, models_resp]

        assert client.verify() is True
        assert mock_get.call_count == 2

    @patch("llm_client.requests.get")
    def test_verify_failure(self, mock_get, client):
        """Test verify returns False when both endpoints fail."""
        mock_get.side_effect = Exception("Connection refused")

        assert client.verify() is False

    def test_base_url_normalization(self):
        """Test trailing slashes and /v1 suffix normalization."""
        c1 = LlamaCppClient(base_url="http://localhost:8080/")
        assert c1.base_url == "http://localhost:8080"

        c2 = LlamaCppClient(base_url="http://localhost:8080/v1")
        assert c2.base_url == "http://localhost:8080"

        c3 = LlamaCppClient(base_url="http://localhost:8080/v1/")
        assert c3.base_url == "http://localhost:8080"

    @patch("llm_client.requests.post")
    def test_api_key_header(self, mock_post):
        """Test that api_key is added to Authorization header."""
        client = LlamaCppClient(base_url="http://localhost:8080", api_key="secret-token")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
        mock_post.return_value = mock_response

        client.ask("test")

        headers = mock_post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer secret-token"


class TestLlamaCppClientDirect:
    """Tests for llama.cpp client in direct GGUF in-process mode."""

    def test_direct_mode_detection(self):
        """Test that providing model_path sets direct mode."""
        client = LlamaCppClient(model_path="models/model.gguf")
        assert client.mode == "direct"

    def test_direct_ask_success(self):
        """Test direct GGUF ask with mock LLM instance."""
        mock_llm = Mock()
        mock_llm.create_chat_completion.return_value = {
            "choices": [{"message": {"content": "direct response"}}]
        }
        client = LlamaCppClient(model_path="models/model.gguf", llm_instance=mock_llm)

        result = client.ask("Hello GGUF")

        assert result == "direct response"
        mock_llm.create_chat_completion.assert_called_once()

    def test_direct_ask_stream_success(self):
        """Test direct GGUF ask_stream with mock LLM instance."""
        mock_llm = Mock()
        mock_llm.create_chat_completion.return_value = [
            {"choices": [{"delta": {"content": "chunk1"}}]},
            {"choices": [{"delta": {"content": "chunk2"}}]},
        ]
        client = LlamaCppClient(model_path="models/model.gguf", llm_instance=mock_llm)

        tokens = list(client.ask_stream("Hello"))

        assert tokens == ["chunk1", "chunk2"]

    @patch("os.path.exists")
    def test_direct_verify_file_missing(self, mock_exists):
        """Test verify returns False when GGUF file does not exist."""
        mock_exists.return_value = False
        client = LlamaCppClient(model_path="models/nonexistent.gguf")

        assert client.verify() is False

    @patch("os.path.exists")
    def test_direct_verify_file_exists_and_importable(self, mock_exists):
        """Test verify returns True when GGUF file exists and llama_cpp is importable."""
        mock_exists.return_value = True
        client = LlamaCppClient(model_path="models/model.gguf")

        with patch.dict("sys.modules", {"llama_cpp": Mock()}):
            assert client.verify() is True

    @patch("os.path.exists")
    def test_direct_verify_missing_import(self, mock_exists):
        """Test verify returns False when llama_cpp is not installed."""
        mock_exists.return_value = True
        client = LlamaCppClient(model_path="models/model.gguf")

        with patch("builtins.__import__", side_effect=ImportError("No module named 'llama_cpp'")):
            assert client.verify() is False

    @patch("os.path.exists")
    def test_direct_ask_missing_package_error(self, mock_exists):
        """Test ask returns error explaining missing package when llama_cpp cannot be imported."""
        mock_exists.return_value = True
        client = LlamaCppClient(model_path="models/model.gguf")

        with patch("builtins.__import__", side_effect=ImportError("No module named 'llama_cpp'")):
            result = client.ask("Test")
            assert "Error" in result
            assert "llama-cpp-python" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
