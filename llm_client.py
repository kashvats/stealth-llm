import abc
import os
import json
import logging
import requests
from typing import Optional, Iterator

logger = logging.getLogger(__name__)

class LLMClient(abc.ABC):
    @abc.abstractmethod
    def ask(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[list] = None) -> str:
        pass

    def ask_stream(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[list] = None) -> Iterator[str]:
        """Streaming variant — yields text chunks as they arrive. Default: single-shot fallback."""
        yield self.ask(prompt, system_prompt=system_prompt, history=history)

    def verify(self) -> bool:
        """Checks if the client can connect to the provider."""
        return True

class MockLLMClient(LLMClient):
    def ask(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[list] = None) -> str:
        return f"Mock Answer to: {prompt[:50]}..."

class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.model = model
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def verify(self) -> bool:
        try:
             headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
             # Minimal test request
             data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5
            }
             response = requests.post(self.base_url, headers=headers, json=data, timeout=5)
             if response.status_code == 200:
                 return True
             logger.error(f"OpenAI Verification Failed: {response.status_code} {response.text}")
             return False
        except Exception as e:
            logger.error(f"OpenAI Verification Error: {e}")
            return False

    def ask(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[list] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            messages.extend(history)
            
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=data, timeout=120)
            if response.status_code != 200:
                return f"Error (OpenAI): {response.status_code} - {response.text}"
                
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"OpenAI Request Failed: {e}")
            return f"Error (OpenAI): {str(e)}"

class OllamaClient(LLMClient):
    def __init__(self, model: str = "llama3.2"):
        self.model = model
        base = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        # Normalise: strip any trailing /api so we always build from the root
        if base.endswith("/api"):
            base = base[:-4]
        self._base = base  # e.g. "http://localhost:11434"

    def _url(self, path: str) -> str:
        return f"{self._base}/api/{path.lstrip('/')}"

    def _keep_alive(self) -> int:
        """Return keep_alive seconds from env, with safe fallback."""
        try:
            return int(os.getenv("OLLAMA_KEEP_ALIVE", "300"))
        except (TypeError, ValueError):
            return 300

    def verify(self) -> bool:
        try:
            response = requests.get(self._url("tags"), timeout=5)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Ollama Verification Failed: {e}")
            return False

    def ask(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[list] = None) -> str:
        url = self._url("chat")
        
        # Construct messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            messages.extend(history)
            
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": self._keep_alive(),
        }
        
        try:
            response = requests.post(url, json=data, timeout=120)
            
            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_msg = error_json["error"]
                except (ValueError, KeyError) as e:
                    logger.debug(f"Could not parse Ollama error JSON: {e}")
                logger.error(f"Ollama API Error ({response.status_code}): {error_msg}")
                return f"Error: {error_msg}"
                
            result = response.json()
            # Response format for /api/chat: {"message": {"content": "..."}}
            return result["message"]["content"]
            
        except Exception as e:
            logger.error(f"Ollama Request Failed: {e}")
            return f"Error (Ollama): {str(e)}"

    def ask_stream(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[list] = None) -> Iterator[str]:
        """Stream response chunks from Ollama as they arrive."""
        url = self._url("chat")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "keep_alive": self._keep_alive(),
        }

        try:
            with requests.post(url, json=data, stream=True, timeout=120) as resp:
                if resp.status_code != 200:
                    yield f"Error (Ollama): {resp.status_code}"
                    return
                for line in resp.iter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Ollama Stream Failed: {e}")
            yield f"Error (Ollama): {str(e)}"

class LlamaCppClient(LLMClient):
    """
    llama.cpp client supporting:
    1. HTTP Server mode (default): Connects to llama-server (or llama-cpp-python server) via OpenAI-compatible endpoints.
    2. Direct GGUF mode: Loads a local .gguf model in-process using llama-cpp-python when model_path is provided.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_path: Optional[str] = None,
        api_key: Optional[str] = None,
        n_ctx: int = 2048,
        mode: Optional[str] = None,
        llm_instance: Optional[object] = None,
    ):
        self.model_path = model_path if model_path is not None else os.getenv("LLAMACPP_MODEL_PATH")
        self.api_key = api_key if api_key is not None else os.getenv("LLAMACPP_API_KEY")
        self.n_ctx = n_ctx
        self._llm_instance = llm_instance

        # Determine mode: "direct" or "server"
        if mode:
            self.mode = mode.lower()
        elif self.model_path:
            self.mode = "direct"
        else:
            self.mode = "server"

        # Normalize base_url for server mode (strip trailing slashes and /v1)
        raw_base = base_url or os.getenv("LLAMACPP_BASE_URL", "http://localhost:8080")
        base = raw_base.rstrip("/")
        if base.endswith("/v1"):
            base = base[:-3]
        self.base_url = base

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _get_direct_llm(self):
        if self._llm_instance is None:
            try:
                from llama_cpp import Llama
            except ImportError:
                raise ImportError(
                    "llama-cpp-python is required for direct GGUF loading. "
                    "Install with: pip install llama-cpp-python"
                )
            if not self.model_path or not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            self._llm_instance = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                verbose=False
            )
        return self._llm_instance

    def verify(self) -> bool:
        """Checks if llama.cpp server is reachable or direct model file is accessible."""
        if self.mode == "direct":
            if not self.model_path or not os.path.exists(self.model_path):
                logger.error(f"LlamaCpp model file not found: {self.model_path}")
                return False
            try:
                import llama_cpp
                return True
            except ImportError:
                logger.error("llama-cpp-python package is not installed.")
                return False
        else:
            headers = self._get_headers()
            try:
                # 1. Try /health
                try:
                    resp = requests.get(f"{self.base_url}/health", headers=headers, timeout=5)
                    if resp.status_code == 200:
                        return True
                except requests.RequestException:
                    pass
                # 2. Fallback to /v1/models
                resp = requests.get(f"{self.base_url}/v1/models", headers=headers, timeout=5)
                return resp.status_code == 200
            except Exception as e:
                logger.error(f"LlamaCpp server verification failed: {e}")
                return False

    def ask(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[list] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        if self.mode == "direct":
            try:
                llm = self._get_direct_llm()
                response = llm.create_chat_completion(
                    messages=messages,
                    stream=False
                )
                return response["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"LlamaCpp direct ask failed: {e}")
                return f"Error (LlamaCpp): {str(e)}"
        else:
            url = f"{self.base_url}/v1/chat/completions"
            headers = self._get_headers()
            data = {
                "messages": messages,
                "stream": False,
            }
            try:
                response = requests.post(url, headers=headers, json=data, timeout=120)
                if response.status_code != 200:
                    error_msg = response.text
                    try:
                        error_json = response.json()
                        if "error" in error_json:
                            err_obj = error_json["error"]
                            error_msg = err_obj.get("message", str(err_obj)) if isinstance(err_obj, dict) else str(err_obj)
                    except Exception:
                        pass
                    logger.error(f"LlamaCpp API Error ({response.status_code}): {error_msg}")
                    return f"Error (LlamaCpp): {error_msg}"
                result = response.json()
                return result["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"LlamaCpp Request Failed: {e}")
                return f"Error (LlamaCpp): {str(e)}"

    def ask_stream(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[list] = None) -> Iterator[str]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        if self.mode == "direct":
            try:
                llm = self._get_direct_llm()
                stream_response = llm.create_chat_completion(
                    messages=messages,
                    stream=True
                )
                for chunk in stream_response:
                    choices = chunk.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        token = delta.get("content", "")
                        if token:
                            yield token
            except Exception as e:
                logger.error(f"LlamaCpp direct stream failed: {e}")
                yield f"Error (LlamaCpp): {str(e)}"
        else:
            url = f"{self.base_url}/v1/chat/completions"
            headers = self._get_headers()
            data = {
                "messages": messages,
                "stream": True,
            }
            try:
                with requests.post(url, headers=headers, json=data, stream=True, timeout=120) as resp:
                    if resp.status_code != 200:
                        yield f"Error (LlamaCpp): {resp.status_code}"
                        return
                    for line in resp.iter_lines():
                        if not line:
                            continue
                        line_str = line.decode("utf-8") if isinstance(line, bytes) else line
                        line_str = line_str.strip()
                        if line_str.startswith("data: "):
                            payload = line_str[6:].strip()
                            if payload == "[DONE]":
                                break
                            try:
                                chunk = json.loads(payload)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    token = delta.get("content", "")
                                    if token:
                                        yield token
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                logger.error(f"LlamaCpp Stream Failed: {e}")
                yield f"Error (LlamaCpp): {str(e)}"

def get_client(api_key: Optional[str] = None, provider: Optional[str] = None, local_model: str = "llama3.2") -> LLMClient:
    """
    Factory to return the best available LLM Client.
    Priority:
    1. Explicit 'provider' argument (openai/ollama/llamacpp)
    2. Environment 'LLM_PROVIDER'
    3. Presence of 'OPENAI_API_KEY' -> OpenAI
    4. Default -> Ollama (Offline)
    """
    # 1. Resolve Provider
    if not provider:
        provider = os.getenv("LLM_PROVIDER")
    
    # 2. auto-detect if still None
    if not provider:
        if api_key or os.getenv("OPENAI_API_KEY"):
            provider = "openai"
        elif os.getenv("LLAMACPP_BASE_URL") or os.getenv("LLAMACPP_MODEL_PATH"):
            provider = "llamacpp"
        else:
            provider = "ollama"
            
    provider = provider.lower()
    logger.info(f"Initializing LLM Client: Provider={provider}")

    # 3. Instantiate & Verify
    client = None
    
    if provider == "openai":
        final_key = api_key if api_key else os.getenv("OPENAI_API_KEY")
        if final_key:
            client = OpenAIClient(final_key)
            if client.verify():
                logger.info("OpenAI Connection Verified.")
                return client
            else:
                logger.error("OpenAI verification failed. Falling back to Ollama/Mock.")
                # Fallthrough to next priority

    if provider in ("llamacpp", "llama.cpp", "llama_cpp"):
        client = LlamaCppClient()
        if client.verify():
            logger.info("LlamaCpp Connection Verified.")
            return client
        else:
            logger.error("LlamaCpp verification failed. Falling back to Mock.")
            return MockLLMClient()
        
    # If OpenAI failed or was not selected, try Ollama
    if provider == "ollama" or not client:
        client = OllamaClient(model=local_model)
        if client.verify():
             logger.info("Ollama Connection Verified.")
             return client
        else:
             logger.error("Ollama verification failed. Is Ollama running?")
    
    # Final Fallback
    logger.warning("All LLM providers failed verification. Using Mock Client.")
    return MockLLMClient()
