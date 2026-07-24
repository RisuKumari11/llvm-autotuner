"""Prompt construction for pass-sequence proposals."""
import json

from ..config import FUNCTION_PASSES, PASS_CFG

POOL = FUNCTION_PASSES + PASS_CFG["loop_passes"]

PASS_DESCRIPTIONS = {
    "sroa": "scalar replacement of aggregates, promotes memory to registers",
    "early-cse": "early common subexpression elimination",
    "instcombine": "algebraic instruction simplification",
    "simplifycfg": "control-flow graph cleanup",
    "reassociate": "reassociates expressions to enable other opts",
    "gvn": "global value numbering, removes redundant computation",
    "sccp": "sparse conditional constant propagation",
    "correlated-propagation": "propagates value info across correlated branches",
    "jump-threading": "threads branches through blocks",
    "adce": "aggressive dead code elimination",
    "dce": "dead code elimination",
    "tailcallelim": "tail call elimination",
    "loop-simplify": "canonicalizes loop form (run before loop passes)",
    "loop-unroll": "unrolls loops",
    "loop-vectorize": "auto-vectorizes loops (SIMD)",
    "slp-vectorizer": "vectorizes straight-line code",
    "loop-rotate": "rotates loops to enable licm/vectorization",
    "licm": "hoists loop-invariant code out of loops",
    "indvars": "canonicalizes induction variables",
    "loop-deletion": "deletes dead loops",
}

SYSTEM = """You are an LLVM optimization expert. You propose pass sequences \
to minimize the executed instruction count of a program. You respond ONLY \
with a JSON object, no prose, no markdown fences."""

def proposal_prompt(bench_name: str, features: dict,
                    history: list[dict] | None = None) -> list[dict]:
    pass_list = "\n".join(f"- {p}: {PASS_DESCRIPTIONS[p]}" for p in POOL)
    user = f"""Program: {bench_name}
Static features of its LLVM IR:
{json.dumps(features, indent=2)}

Available passes (use ONLY these exact names):
{pass_list}

Propose ONE pass sequence of 12 to 24 passes (repetition allowed, order matters).
Typical good pipelines: cleanup passes first (sroa, early-cse, instcombine, \
simplifycfg), then loop canonicalization (loop-simplify, loop-rotate), then \
loop optimization (licm, indvars, loop-unroll), then redundancy elimination \
(gvn, sccp), then vectorization (loop-vectorize, slp-vectorizer), then final \
cleanup (instcombine, simplifycfg, adce).

Respond with exactly this JSON shape:
{{"reasoning": "<one short sentence>", "passes": ["pass1", "pass2", ...]}}"""
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": user}]
    if history:
        msgs.append({"role": "user", "content":
            "Previously measured results for this program (lower instr is better):\n"
            + json.dumps(history, indent=2)
            + "\nPropose a NEW sequence you expect to beat the best one. Same JSON shape."})
    return msgs