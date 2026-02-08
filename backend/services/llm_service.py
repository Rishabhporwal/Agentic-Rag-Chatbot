import logging
import requests
from typing import List, Dict, Any, Optional
import time


logger = logging.getLogger("backend.llm_service")


class LLMService:
    """Service for LLM operations using Ollama."""

    def __init__(self, base_url: str, model: str):
        """
        Initialize the LLM service.

        Args:
            base_url: Base URL for Ollama API
            model: Name of the LLM model
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        logger.info(f"LLMService initialized (model={model})")

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": False
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

        except Exception as e:
            logger.error(f"Generation failed: {str(e)}")
            raise RuntimeError(f"LLM generation failed: {str(e)}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate response from chat messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "num_predict": max_tokens,
            "stream": False
        }

        try:
            response = requests.post(
                self.chat_url,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")

        except Exception as e:
            logger.error(f"Chat generation failed: {str(e)}")
            raise RuntimeError(f"LLM chat failed: {str(e)}")

    def score_relevance(self, query: str, text: str) -> float:
        """
        Score the relevance of text to a query using LLM.

        Args:
            query: Query text
            text: Text to score

        Returns:
            Relevance score between 0 and 1
        """
        prompt = f"""Rate the relevance of the following text to the query on a scale of 0 to 1.
Only respond with a number between 0 and 1.

Query: {query}

Text: {text[:500]}

Relevance score:"""

        try:
            response = self.generate(prompt, temperature=0.0, max_tokens=10)
            # Extract number from response
            score_str = response.strip().split()[0]
            score = float(score_str)
            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.warning(f"Failed to score relevance: {str(e)}")
            return 0.5  # Default to neutral score
