import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import OpenAI
from config import AISA_API_KEY, AISA_BASE_URL, AISA_MODEL


class LLMProvider:
    """OpenAI-SDK-compatible wrapper targeting the AISA gateway."""

    def __init__(self):
        self._key = AISA_API_KEY
        self._base_url = AISA_BASE_URL
        self.model = AISA_MODEL
        self._client = None

    def _get_client(self):
        if not self._key:
            raise RuntimeError(
                "AISA_API_KEY not configured. Add it to .env:\n"
                "  AISA_API_KEY=your_key_here\n"
                "  AISA_BASE_URL=https://api.aisa.one/v1\n"
                "  AISA_MODEL=deepseek/deepseek-chat"
            )
        if self._client is None:
            self._client = OpenAI(api_key=self._key, base_url=self._base_url)
        return self._client

    def complete(self, system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
        from openai import InternalServerError, AuthenticationError
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content
        except InternalServerError as exc:
            if "model_not_found" in str(exc) or "503" in str(exc):
                raise RuntimeError(
                    f"Model '{self.model}' is not available on your AISA account.\n"
                    f"Update AISA_MODEL in your .env file to a model you have access to.\n"
                    f"Check your AISA dashboard for available models.\n"
                    f"Original error: {exc}"
                ) from exc
            raise
        except AuthenticationError as exc:
            raise RuntimeError(
                f"AISA authentication failed. Check that AISA_API_KEY is correct in .env.\n"
                f"Original error: {exc}"
            ) from exc
