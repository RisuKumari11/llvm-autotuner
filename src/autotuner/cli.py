import time
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from .config import BENCH_CFG
from .baselines import build_baseline, LEVELS
from .measure import instruction_count, wall_clock
from . import store

app = typer.Typer()
console = Console()
WORK = Path("/tmp/autotuner")

@app.command()
def baselines(callgrind: bool = True, timing: bool = False):
    """Measure -O0/-O2/-O3/-Os across all benchmarks."""
    rows = []
    for b in BENCH_CFG["benchmarks"]:
        for lvl in LEVELS:
            row = {"bench": b["name"], "level": lvl, "ts": time.time()}
            if callgrind:
                bin_cg = build_baseline(b["path"], lvl,
                                        BENCH_CFG["dataset_callgrind"],
                                        WORK / b["name"] / "cg")
                row["instr"] = instruction_count(bin_cg)
            if timing:
                bin_wc = build_baseline(b["path"], lvl,
                                        BENCH_CFG["dataset_wallclock"],
                                        WORK / b["name"] / "wc")
                wc = wall_clock(bin_wc)
                row.update(median_s=wc.median_s, stddev_s=wc.stddev_s)
            rows.append(row)
            console.print(f"[green]done[/] {b['name']} -{lvl} {row.get('instr','')}")
    store.append(rows, "baselines")

@app.command()
def report():
    """Print baseline table with speedups vs O0."""
    df = store.load("baselines")
    df = df.dropna(subset=["instr"])
    df = df.drop_duplicates(["bench", "level"], keep="last")
    piv = df.pivot(index="bench", columns="level", values="instr")
    t = Table(title="Instruction count (lower is better)")
    t.add_column("bench")
    for lvl in LEVELS: 
        t.add_column(lvl, justify="right")
    t.add_column("O2/O0", justify="right")
    for bench, r in piv.iterrows():
        t.add_row(bench, *(f"{int(r[level]):,}" for level in LEVELS), f"{r['O0']/r['O2']:.2f}x")
    console.print(t)

@app.command()
def search(method: str = "random", budget: int = 60, seed: int = 0):
    """Run a search method across all benchmarks, log every evaluation."""
    from .search.evaluate import Evaluator
    from .search.random_search import random_search
    from .search.hillclimb import hill_climb   # exists after Day 3
    all_rows = []
    for b in BENCH_CFG["benchmarks"]:
        ev = Evaluator(b["name"], b["path"])
        if method == "random":
            rows = random_search(ev, budget, seed)
        elif method == "hillclimb":
            from .search.hillclimb import hill_climb
            rows = hill_climb(ev, budget, seed)
        else:
            raise typer.BadParameter(method)
        all_rows += rows
        best = min((r["instr"] for r in rows if r["instr"] is not None), default=None)
        console.print(f"[green]{b['name']}[/] best={best}")
    store.append(all_rows, f"search_{method}") 
  
@app.command()
def compare():
    """Final comparison table: O2/O3 baselines vs search methods."""
    from .stats import geomean
    base = store.load("baselines")
    base = base.dropna(subset=["instr"])
    base = base.drop_duplicates(
        ["bench","level"],
        keep="last"
    )
    base = base.pivot(index="bench", columns="level", values="instr")

    frames = []
    for m in ("random", "hillclimb", "llm_oneshot"):
        df = store.load(f"search_{m}")
        best = (df.dropna(subset=["instr"])
                  .groupby("bench")["instr"].min().rename(m))
        frames.append(best)
    tbl = base.join(frames)

    t = Table(title="Best instruction count per method (lower is better)")
    for col in ["bench", "O2", "O3", "random", "hillclimb",
                "llm_oneshot",
                "rand/O2", "hc/O2", "llm/O2",
                "beats O3?"]:
        t.add_column(col, justify="right")
    for bench, r in tbl.iterrows():
        t.add_row(
            bench,
            f"{int(r['O2']):,}",
            f"{int(r['O3']):,}",
            f"{int(r['random']):,}",
            f"{int(r['hillclimb']):,}",
            f"{int(r['llm_oneshot']):,}",
            f"{r['O2']/r['random']:.3f}x",
            f"{r['O2']/r['hillclimb']:.3f}x",
            f"{r['O2']/r['llm_oneshot']:.3f}x",
            "yes" if r["hillclimb"] < r["O3"] else "no"
        )
    console.print(t)
    for m in ("random", "hillclimb", "llm_oneshot"):
        # vals = (tbl["O2"] / tbl[m]).values
        # print("DEBUG", m, vals)

        # g = geomean(vals)

        # print("DEBUG g =", g)
        g = geomean((tbl["O2"] / tbl[m]).values)
        # console.print(
        #     f"geomean speedup vs O2 ({m}): [bold]{g:.3f}x[/]"
        # )
        console.print(f"geomean speedup vs O2 ({m}): {g:.3f}x")
        # console.print(f"benchmarks where hillclimb beats O3: "
        #             f"{int((tbl['hillclimb'] < tbl['O3']).sum())}/{len(tbl)}")
        beats = int((tbl["hillclimb"] < tbl["O3"]).sum())
        console.print(f"benchmarks where hillclimb beats O3: {beats}/{len(tbl)}")
llm = store.load("search_llm_oneshot")
valid_rate = llm["passes"].ne("").mean()
console.print(f"LLM valid-proposal rate: {valid_rate:.0%}")
console.print(f"LLM mean attempts per accepted proposal: "
                f"{llm.loc[llm['passes'].ne(''), 'llm_attempts'].mean():.2f}")
    
@app.command()
def validate():
    """Wall-clock check: does the instruction-count winner also win real time?"""
    from .search.evaluate import WORK
    from .ir import emit_linked_bc
    from .compile import compile_with_passes
    from .measure import wall_clock
    from .baselines import build_baseline

    df = store.load("search_hillclimb").dropna(subset=["instr"])
    rows = []
    for b in BENCH_CFG["benchmarks"]:
        d = df[df.bench == b["name"]]
        if d.empty: 
            continue
        best_seq = d.loc[d["instr"].idxmin(), "passes"].split(",")
        wd = WORK / b["name"] / "validate"
        bc = emit_linked_bc(b["path"], BENCH_CFG["dataset_wallclock"], wd)
        tuned = compile_with_passes(bc, best_seq, wd / "bin_tuned")
        o2 = build_baseline(b["path"], "O2", BENCH_CFG["dataset_wallclock"], wd)
        wt, wo = wall_clock(tuned), wall_clock(o2)
        rows.append({"bench": b["name"], "tuned_median": wt.median_s,
                     "o2_median": wo.median_s,
                     "speedup": wo.median_s / wt.median_s})
        console.print(f"{b['name']}: {wo.median_s/wt.median_s:.3f}x vs O2 (wall-clock)")
    store.append(rows, "wallclock_validation")
@app.command()
def llm_search(budget: int = 60, backend: str = "ollama",
               model: str = "", temperature: float = 0.8, seed: int = 0):
    """LLM one-shot proposals as a candidate source, budget-matched to search."""
    import time as _t
    from .search.evaluate import Evaluator
    from .llm.features import ir_features
    from .llm.agent import propose

    all_rows = []
    for b in BENCH_CFG["benchmarks"]:
        ev = Evaluator(b["name"], b["path"])
        feats = ir_features(ev._linked)
        best = None
        while ev.evals < budget:
            seq, attempts = propose(b["name"], feats, backend=backend,
                                    model=model or None,
                                    temperature=temperature)
            if seq is None:
                ev.evals += 1          # failed proposal still costs budget
                val = None
            else:
                val = ev.score(seq)
            if val is not None and (best is None or val < best):
                best = val
            all_rows.append({
                "method": "llm_oneshot", "bench": b["name"], "seed": seed,
                "eval_idx": ev.evals,
                "passes": ",".join(seq) if seq else "",
                "instr": val, "best_so_far": best,
                "llm_attempts": attempts, "ts": _t.time(),
            })
        console.print(f"[green]{b['name']}[/] best={best}")
    store.append(all_rows, "search_llm_oneshot")
    
if __name__ == "__main__":
    app()