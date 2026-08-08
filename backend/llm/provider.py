"""
NVIDIA NIM Provider for Llama 3.1 70B Instruct
================================================
Wraps the NVIDIA NIM API (OpenAI-compatible) so every other module in
backend/llm/ talks to a single provider, never to the HTTP layer directly.
"""

from openai import OpenAI

try:
    from config.settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL
    from config.settings import LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TOP_P
except ImportError:
    from backend.config.settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL
    from backend.config.settings import LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TOP_P


class LLMProvider:
    """
    Single connection to NVIDIA NIM hosting meta/llama-3.1-70b-instruct.
    All SYRA modules call this instead of making raw HTTP requests.
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
    ):
        self.api_key = api_key or NVIDIA_API_KEY
        self.base_url = base_url or NVIDIA_BASE_URL
        self.model = model or NVIDIA_MODEL

        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY not set. "
                "Create a .env file with: NVIDIA_API_KEY=nvapi-YOUR_KEY_HERE\n"
                "Get your key at: https://build.nvidia.com/meta/llama-3_1-70b-instruct"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=30.0,
            max_retries=1,
        )

    def chat(
        self,
        messages: list,
        temperature: float = None,
        max_tokens: int = None,
        top_p: float = None,
    ) -> str:
        """
        Sends a chat completion request to Llama 3.1 70B and returns the
        assistant's text response.

        Parameters
        ----------
        messages : list of dict
            OpenAI-format messages, e.g.:
            [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or LLM_TEMPERATURE,
            max_tokens=max_tokens or LLM_MAX_TOKENS,
            top_p=top_p or LLM_TOP_P,
        )

        return response.choices[0].message.content

    def chat_stream(
        self,
        messages: list,
        temperature: float = None,
        max_tokens: int = None,
        top_p: float = None,
    ):
        """
        Streams the response token-by-token (for real-time UI display).
        Yields each text chunk as it arrives.
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or LLM_TEMPERATURE,
            max_tokens=max_tokens or LLM_MAX_TOKENS,
            top_p=top_p or LLM_TOP_P,
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
