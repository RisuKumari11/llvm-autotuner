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
    df = store.load("baselines").drop_duplicates(["bench", "level"], keep="last")
    piv = df.pivot(index="bench", columns="level", values="instr")
    t = Table(title="Instruction count (lower is better)")
    t.add_column("bench")
    for lvl in LEVELS: 
        t.add_column(lvl, justify="right")
    t.add_column("O2/O0", justify="right")
    for bench, r in piv.iterrows():
        t.add_row(bench, *(f"{int(r[level]):,}" for level in LEVELS), f"{r['O0']/r['O2']:.2f}x")
    console.print(t)

if __name__ == "__main__":
    app()