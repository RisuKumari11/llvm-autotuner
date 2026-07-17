from pathlib import Path
import yaml
import os

ROOT = Path(__file__).resolve().parents[2]

def load_yaml(name: str) -> dict:
    with open(ROOT / "configs" / name) as f:
        return yaml.safe_load(f)

BENCH_CFG = load_yaml("benchmarks.yaml")
PASS_CFG = load_yaml("passes.yaml")
POLYBENCH = Path(
    os.environ.get(
        "POLYBENCH_ROOT",
        BENCH_CFG["polybench_root"]
    )
)
LOOP_PASSES = set(PASS_CFG["loop_passes"])
FUNCTION_PASSES = list(PASS_CFG["function_passes"])