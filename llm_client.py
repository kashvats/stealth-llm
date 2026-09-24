import abc
import os
import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class LLMClient(abc.ABC):
    @abc.abstractmethod
    def ask(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[list] = None) -> str:
        pass
        
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
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def verify(self) -> bool:
        try:
            # Check tags to see if Ollama is up AND model exists
            # Ensure we hit /api/tags
            url = f"{self.base_url}/api/tags"
            if "/api" in self.base_url: 
                url = f"{self.base_url}/tags" # Avoid double /api/api
                
            response = requests.get(url, timeout=5)
            
            if response.status_code == 404:
                 # Fallback to simple root check if tags fails
                 root_url = self.base_url.replace("/api", "")
                 response = requests.get(root_url, timeout=5)
            
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Ollama Verification Failed: {e}")
            return False

    def ask(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[list] = None) -> str:
        # Use /api/chat which is better for chat models than /api/generate
        url = f"{self.base_url}/api/chat"
        if "/api" in self.base_url:
            url = f"{self.base_url}/chat"
        
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
            "keep_alive": -1  # Keep model in memory indefinitely for instant response
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

def get_client(api_key: Optional[str] = None, provider: Optional[str] = None, local_model: str = "llama3.2") -> LLMClient:
    # ...
    """
    Factory to return the best available LLM Client.
    Priority:
    1. Explicit 'provider' argument (openai/ollama)
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
