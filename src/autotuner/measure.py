"""Measure a binary: deterministic instruction count and wall-clock stats."""
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

@dataclass
class WallClock:
    median_s: float
    mean_s: float
    stddev_s: float
    runs: int

def instruction_count(binary: Path, timeout: int = 600) -> int:
    """Callgrind Ir count. Deterministic. Use MINI/SMALL dataset builds only."""
    with tempfile.NamedTemporaryFile(suffix=".cg") as f:
        subprocess.run(
            ["valgrind", "--tool=callgrind", f"--callgrind-out-file={f.name}", str(binary)],
            check=True, capture_output=True, timeout=timeout)
        text = Path(f.name).read_text()
    m = re.search(r"^summary:\s+(\d+)", text, re.MULTILINE)
    if not m:
        raise RuntimeError(f"no callgrind summary for {binary}")
    return int(m.group(1))

def wall_clock(binary: Path, min_runs: int = 10, warmup: int = 3) -> WallClock:
    with tempfile.NamedTemporaryFile(suffix=".json") as f:
        subprocess.run(
            ["hyperfine", "--warmup", str(warmup), "--min-runs", str(min_runs),
             "--export-json", f.name, f"taskset -c 0 {binary}"],
            check=True, capture_output=True)
        data = json.loads(Path(f.name).read_text())["results"][0]
    return WallClock(median_s=data["median"], mean_s=data["mean"],
                     stddev_s=data["stddev"], runs=len(data["times"]))