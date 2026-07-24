from src.autotuner import store
from src.autotuner.stats import geomean
import pandas as pd

# Must match the --benches value used when generating search_llm_loop_h2.parquet
# and search_llm_loop_nofeat.parquet (see command below).
# python -m src.autotuner.cli llm-loop \
#   --budget 60 --history-size 2 \
#   --benches gemm,atax,jacobi-2d,correlation,mvt \
#   --seed 0
ABLATION_BENCHES = [
    "gemm",
    "atax",
    "jacobi-2d",
    "correlation",
    "mvt",
]

base = (
    store.load("baselines")
    .dropna(subset=["instr"])
    .drop_duplicates(["bench", "level"], keep="last")
    .pivot(index="bench", columns="level", values="instr")
)

methods = {
    "LLM OneShot": "search_llm_oneshot",
    "LLM Loop h=8": "search_llm_loop",
    "LLM Loop h=2": "search_llm_loop_h2",
    "LLM No Features": "search_llm_loop_nofeat",
}

print()
print("Method".ljust(20), "Geomean vs O2")
print("-" * 40)

for name, file in methods.items():

    df = store.load(file)

    best = (
        df.dropna(subset=["instr"])
          .groupby("bench")["instr"]
          .min()
    )

    best = best.loc[
        best.index.intersection(ABLATION_BENCHES)
    ]

    vals = (
        base.loc[best.index, "O2"] / best
    ).values

    g = geomean(vals)

    print(name.ljust(20), f"{g:.3f}x")