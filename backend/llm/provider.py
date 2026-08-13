"""
NVIDIA NIM Provider for Llama 3.1 70B Instruct
================================================
Wraps the NVIDIA NIM API (OpenAI-compatible) so every other module in
backend/llm/ talks to a single provider, never to the HTTP layer directly.
"""

from openai import OpenAI

try:
    from config.settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL, NVIDIA_FALLBACK_MODEL
    from config.settings import LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TOP_P, LLM_TIMEOUT, LLM_MAX_RETRIES
except ImportError:
    from backend.config.settings import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_MODEL, NVIDIA_FALLBACK_MODEL
    from backend.config.settings import LLM_TEMPERATURE, LLM_MAX_TOKENS, LLM_TOP_P, LLM_TIMEOUT, LLM_MAX_RETRIES


class LLMProvider:
    """
    Single connection to NVIDIA NIM hosting meta/llama-3.1-70b-instruct
    with fast automatic fallback to meta/llama-3.1-8b-instruct.
    All SYRA modules call this instead of making raw HTTP requests.
    """

    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        fallback_model: str = None,
    ):
        self.api_key = api_key or NVIDIA_API_KEY
        self.base_url = base_url or NVIDIA_BASE_URL
        self.model = model or NVIDIA_MODEL
        self.fallback_model = fallback_model or NVIDIA_FALLBACK_MODEL

        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY not set. "
                "Create a .env file with: NVIDIA_API_KEY=nvapi-YOUR_KEY_HERE\n"
                "Get your key at: https://build.nvidia.com/meta/llama-3_1-70b-instruct"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=float(LLM_TIMEOUT),
            max_retries=int(LLM_MAX_RETRIES),
        )

    def chat(
        self,
        messages: list,
        temperature: float = None,
        max_tokens: int = None,
        top_p: float = None,
    ) -> str:
        """
        Sends a chat completion request to Llama 3.1 and returns the
        assistant's text response, with automatic fallback if primary model times out.
        """
        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        last_error = None
        for i, current_model in enumerate(models_to_try):
            try:
                req_timeout = 4.0 if (i == 0 and len(models_to_try) > 1) else float(LLM_TIMEOUT)
                response = self.client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    temperature=temperature or LLM_TEMPERATURE,
                    max_tokens=max_tokens or LLM_MAX_TOKENS,
                    top_p=top_p or LLM_TOP_P,
                    timeout=req_timeout,
                )
                content = response.choices[0].message.content
                if content:
                    return content.strip()
            except Exception as exc:
                last_error = exc
                print(f"[LLMProvider] Model '{current_model}' call failed ({exc.__class__.__name__}: {exc}). Trying next...")

        if last_error:
            raise last_error
        raise RuntimeError("No LLM response generated")

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
        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        for current_model in models_to_try:
            try:
                stream = self.client.chat.completions.create(
                    model=current_model,
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
                return
            except Exception as exc:
                print(f"[LLMProvider] Stream from '{current_model}' failed: {exc}")
