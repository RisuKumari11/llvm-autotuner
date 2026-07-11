"""Random search over fixed-length pass sequences."""
import random
import time

from ..config import FUNCTION_PASSES, PASS_CFG
from .evaluate import Evaluator

POOL = FUNCTION_PASSES + PASS_CFG["loop_passes"]

def sample_sequence(rng: random.Random, min_len: int = 12, max_len: int = 24) -> list[str]:
    n = rng.randint(min_len, max_len)
    return [rng.choice(POOL) for _ in range(n)]

def random_search(ev: Evaluator, budget: int, seed: int) -> list[dict]:
    """Returns one log row per evaluation."""
    rng = random.Random(seed)
    rows, best = [], None
    while ev.evals < budget:
        seq = sample_sequence(rng)
        val = ev.score(seq)
        if val is not None and (best is None or val < best):
            best = val
        rows.append({
            "method": "random", "bench": ev.bench_name, "seed": seed,
            "eval_idx": ev.evals, "passes": ",".join(seq),
            "instr": val, "best_so_far": best, "ts": time.time(),
        })
    return rows