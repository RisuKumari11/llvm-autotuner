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

"""LLM-in-the-loop: propose -> measure -> feed results back -> repeat."""
def feedback_loop(ev, bench_name: str, features: dict,
                  budget: int, proposals_per_round: int = 5,
                  history_size: int = 8, backend: str = "ollama",
                  model: str | None = None, temperature: float = 0.8,
                  seed: int = 0) -> list[dict]:
    """
    Rounds of: sample K proposals -> score all -> append best/worst results
    to history -> next round conditions on measurements.
    Budget-matched via ev.evals like every other method.
    """
    rows, history, best = [], [], None
    round_idx = 0
    while ev.evals < budget:
        round_idx += 1
        for _ in range(proposals_per_round):
            if ev.evals >= budget:
                break
            seq, attempts = propose(bench_name, features,
                                    history=history or None,
                                    backend=backend, model=model,
                                    temperature=temperature)
            if seq is None:
                ev.evals += 1
                val = None
            else:
                val = ev.score(seq)
            if val is not None and (best is None or val < best):
                best = val
            rows.append({
                "method": "llm_loop", "bench": bench_name, "seed": seed,
                "eval_idx": ev.evals, "round": round_idx,
                "passes": ",".join(seq) if seq else "",
                "instr": val, "best_so_far": best,
                "llm_attempts": attempts, "ts": time.time(),
            })
        # rebuild history: best results so far, plus one worst as a negative example
        scored = [(r["instr"], r["passes"]) for r in rows if r["instr"] is not None]
        scored.sort()
        history = [{"passes": p, "instr": v} for v, p in scored[:history_size - 1]]
        if len(scored) > history_size:
            v, p = scored[-1]
            history.append({"passes": p, "instr": v, "note": "worst measured, avoid patterns like this"})
    return rows