"""LLM-guided candidate generation."""
import time
from .client import chat, LLMError
from .prompts import proposal_prompt
from .parse import parse_proposal

def propose(bench_name: str, features: dict, history=None,
            backend="ollama", model=None, max_retries=3,
            temperature=0.7) -> tuple[list[str] | None, int]:
    """Returns (passes or None, attempts_used)."""
    msgs = proposal_prompt(bench_name, features, history)
    for attempt in range(1, max_retries + 1):
        try:
            raw = chat(msgs, backend=backend, model=model,
                       temperature=temperature)
            return parse_proposal(raw).passes, attempt
        except (LLMError, ValueError) as e:
            msgs.append({"role": "user", "content":
                f"Your previous response was invalid ({e}). "
                "Respond with ONLY the JSON object, exact pass names from the list."})
            time.sleep(1)
    return None, max_retries