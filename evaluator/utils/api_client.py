import requests
from typing import Dict, Any, List


class BackendAPIClient:
    """Client for interacting with the backend API."""

    def __init__(self, base_url: str, api_prefix: str = "/v1"):
        """
        Initialize API client.

        Args:
            base_url: Base URL of the backend
            api_prefix: API version prefix
        """
        self.base_url = base_url.rstrip('/')
        self.api_prefix = api_prefix
        self.chat_url = f"{self.base_url}{self.api_prefix}/chat/completions"

    def query(self, question: str, session_id: str = None) -> Dict[str, Any]:
        """
        Send a query to the backend.

        Args:
            question: Question to ask
            session_id: Optional session ID

        Returns:
            Response dictionary
        """
        payload = {
            "model": "agentic-rag",
            "messages": [{"role": "user", "content": question}],
            "session_id": session_id
        }

        response = requests.post(self.chat_url, json=payload, timeout=120)
        response.raise_for_status()

        return response.json()

    def extract_response_data(self, api_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant data from API response.

        Args:
            api_response: Full API response

        Returns:
            Extracted data
        """
        answer = api_response["choices"][0]["message"]["content"]
        citations = api_response.get("citations", [])

        # Extract contexts from citations
        contexts = [citation["content"] for citation in citations]

        return {
            "answer": answer,
            "contexts": contexts,
            "citations": citations
        }
