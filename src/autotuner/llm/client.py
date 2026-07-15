"""LLM client: Ollama locally, OpenRouter as fallback. One interface."""
import json
import os
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class LLMError(Exception):
    pass

def _post(url: str, payload: dict, headers: dict, timeout: int = 180) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def chat(messages: list[dict],
         backend: str = "ollama",
         model: str | None = None,
         temperature: float = 0.7) -> str:
    """messages: [{'role': 'system'|'user'|'assistant', 'content': str}, ...]"""
    try:
        if backend == "ollama":
            payload = {"model": model or "qwen2.5-coder:3b",
                       "messages": messages, "stream": False,
                       "options": {"temperature": temperature}}
            return _post(OLLAMA_URL, payload, {})["message"]["content"]
        elif backend == "openrouter":
            key = os.environ["OPENROUTER_API_KEY"]
            payload = {"model": model or "qwen/qwen-2.5-coder-32b-instruct",
                       "messages": messages, "temperature": temperature}
            out = _post(OPENROUTER_URL, payload,
                        {"Authorization": f"Bearer {key}"})
            return out["choices"][0]["message"]["content"]
        raise ValueError(backend)
    except Exception as e:
        raise LLMError(f"{backend} call failed: {e}") from e