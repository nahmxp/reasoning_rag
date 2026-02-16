"""
Ollama client wrapper for LLM and embedding operations
"""
import requests
import json
import logging
from typing import List, Dict, Any, Optional
import config

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = config.OLLAMA_BASE_URL):
        self.base_url = base_url
        self.embedding_model = config.EMBEDDING_MODEL
        self.llm_model = config.LLM_MODEL
        self.fast_llm = config.FAST_LLM_MODEL
    
    def generate(self, prompt: str, model: Optional[str] = None, 
                 temperature: float = config.LLM_TEMPERATURE,
                 stream: bool = False, system: Optional[str] = None) -> str:
        """
        Generate text using Ollama LLM
        
        Args:
            prompt: Input prompt
            model: Model name (defaults to config.LLM_MODEL)
            temperature: Sampling temperature
            stream: Whether to stream response
            system: System prompt
        
        Returns:
            Generated text
        """
        model = model or self.llm_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "top_p": config.LLM_TOP_P,
                "top_k": config.LLM_TOP_K,
                "num_predict": config.MAX_TOKENS
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300  # 5 minutes timeout for large responses
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '')
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating text with Ollama: {e}")
            raise
    
    def generate_stream(self, prompt: str, model: Optional[str] = None,
                       temperature: float = config.LLM_TEMPERATURE,
                       system: Optional[str] = None):
        """
        Stream generate text using Ollama LLM
        
        Yields:
            Text chunks as they are generated
        """
        model = model or self.llm_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "top_p": config.LLM_TOP_P,
                "top_k": config.LLM_TOP_K,
                "num_predict": config.MAX_TOKENS
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=300
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if 'response' in chunk:
                        yield chunk['response']
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error streaming text with Ollama: {e}")
            raise
    
    def get_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Get embedding vector for text
        
        Args:
            text: Input text
            model: Embedding model name
        
        Returns:
            Embedding vector
        """
        model = model or self.embedding_model
        
        payload = {
            "model": model,
            "prompt": text
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('embedding', [])
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting embedding from Ollama: {e}")
            raise
    
    def get_embeddings_batch(self, texts: List[str], 
                            model: Optional[str] = None) -> List[List[float]]:
        """
        Get embeddings for multiple texts
        
        Args:
            texts: List of input texts
            model: Embedding model name
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = self.get_embedding(text, model)
            embeddings.append(embedding)
        
        return embeddings
    
    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None,
             temperature: float = config.LLM_TEMPERATURE) -> str:
        """
        Chat completion using Ollama
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name
            temperature: Sampling temperature
        
        Returns:
            Assistant response
        """
        model = model or self.llm_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": config.LLM_TOP_P,
                "top_k": config.LLM_TOP_K
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('message', {}).get('content', '')
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in chat with Ollama: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []


logger.info("Ollama client initialized")

