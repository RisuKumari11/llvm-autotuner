"""Headline figure: geomean speedup vs -O2 per method, plus convergence."""
import matplotlib.pyplot as plt
import pandas as pd
from src.autotuner import store
from src.autotuner.stats import geomean

base = (
    store.load("baselines")
    .dropna(subset=["instr"])
    .drop_duplicates(["bench","level"], keep="last")
    .pivot(index="bench", columns="level", values="instr")
)
methods = ["random", "hillclimb", "llm_oneshot", "llm_loop"]
labels = ["Random", "Hill-climb", "LLM one-shot", "LLM + feedback"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# left: geomean speedup vs O2 and O3 reference lines
gms = []
for m in methods:
    best = store.load(f"search_{m}").dropna(subset=["instr"]).groupby("bench")["instr"].min()
    gms.append(geomean((base.loc[best.index, "O2"] / best).values))
ax1.bar(labels, gms, color=["tab:blue", "tab:orange", "tab:green", "tab:red"])
ax1.axhline(1.0, ls="--", c="gray", label="-O2")
o3 = geomean((base["O2"] / base["O3"]).values)
ax1.axhline(o3, ls=":", c="black", label="-O3")
ax1.set_ylabel("Geomean speedup vs -O2 (instruction count)")
ax1.legend()

# right: mean convergence across benchmarks
for m, lbl in zip(methods, labels):
    df = store.load(f"search_{m}").dropna(subset=["best_so_far"])
    # normalize per benchmark by its O2 count, then average the curves
    df = df.merge(base["O2"].rename("o2"), left_on="bench", right_index=True)
    df["rel"] = df["best_so_far"] / df["o2"]
    curve = df.groupby("eval_idx")["rel"].mean()
    ax2.plot(curve.index, curve.values, label=lbl)
ax2.axhline(1.0, ls="--", c="gray")
ax2.set_xlabel("Evaluations"); ax2.set_ylabel("Best-so-far / -O2 (mean)")
ax2.legend()
fig.tight_layout()
fig.savefig("plots/headline.png", dpi=150)