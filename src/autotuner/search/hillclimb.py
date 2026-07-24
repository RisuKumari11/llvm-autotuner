"""First-improvement hill climbing over pass sequences."""
import random
import time

from .evaluate import Evaluator
from .random_search import POOL, sample_sequence

# A hand-built O2-flavored starting point using only passes from our pool.
O2_LIKE = [
    "sroa", "early-cse", "simplifycfg", "instcombine",
    "loop-simplify", "loop-rotate", "licm", "indvars",
    "loop-unroll", "gvn", "sccp", "adce",
    "loop-vectorize", "slp-vectorizer", "instcombine", "simplifycfg",
]

def mutate(seq: list[str], rng: random.Random) -> list[str]:
    s = list(seq)
    op = rng.choice(["replace", "insert", "delete", "swap"])
    if op == "replace" and s:
        s[rng.randrange(len(s))] = rng.choice(POOL)
    elif op == "insert":
        s.insert(rng.randrange(len(s) + 1), rng.choice(POOL))
    elif op == "delete" and len(s) > 4:
        del s[rng.randrange(len(s))]
    elif op == "swap" and len(s) > 1:
        i, j = rng.sample(range(len(s)), 2)
        s[i], s[j] = s[j], s[i]
    return s

def hill_climb(ev: Evaluator, budget: int, seed: int,
               restart_after: int = 15) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    current, cur_val = list(O2_LIKE), ev.score(O2_LIKE)
    best = cur_val
    stale = 0
    rows.append({
        "method": "hillclimb",
        "bench": ev.bench_name,
        "seed": seed,
        "eval_idx": ev.evals,
        "passes": ",".join(current),
        "instr": cur_val,
        "best_so_far": best,
        "ts": time.time(),
    })
    while ev.evals < budget:
        cand = mutate(current, rng)
        before = ev.evals
        val = ev.score(cand)
        # Cached candidates do not consume an evaluation budget.
        # Skip logging them so eval_idx remains unique.
        if before == ev.evals:
            continue
        improved = val is not None and (cur_val is None or val < cur_val)
        if improved:
            current, cur_val, stale = cand, val, 0
        else:
            stale += 1
        if val is not None and (best is None or val < best):
            best = val
        rows.append({
            "method": "hillclimb",
            "bench": ev.bench_name,
            "seed": seed,
            "eval_idx": ev.evals,
            "passes": ",".join(cand),
            "instr": val,
            "best_so_far": best,
            "ts": time.time(),
        })    
        if stale >= restart_after and ev.evals < budget:            # random restart to escape plateaus
            current = sample_sequence(rng)
            before = ev.evals
            cur_val = ev.score(current)
            stale = 0
            if before != ev.evals:
                if cur_val is not None and (best is None or cur_val < best):
                    best = cur_val
                rows.append({
                    "method": "hillclimb",
                    "bench": ev.bench_name,
                    "seed": seed,
                    "eval_idx": ev.evals,
                    "passes": ",".join(current),
                    "instr": cur_val,
                    "best_so_far": best,
                    "ts": time.time(),
                    "event": "restart",
                })  

    return rows