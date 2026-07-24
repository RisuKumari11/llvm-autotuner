"""Build -O0/-O2/-O3/-Os reference binaries directly with clang."""
import subprocess
from pathlib import Path

from .config import POLYBENCH

CLANG = "clang"
# LEVELS = ["O0", "O2", "O3", "Os"]
LEVELS = ["O2", "O3"]

def build_baseline(bench_path: str, level: str, dataset: str, workdir: Path) -> Path:
    workdir.mkdir(parents=True, exist_ok=True)
    kdir = POLYBENCH / bench_path
    kernel_c = next(kdir.glob("*.c"))
    out = workdir / f"bin_{level}"
    subprocess.run(
        [CLANG, f"-{level}",
         "-I", str(POLYBENCH / "utilities"), "-I", str(kdir),
         f"-D{dataset}", "-DPOLYBENCH_TIME",
         str(POLYBENCH / "utilities" / "polybench.c"), str(kernel_c),
         "-lm", "-o", str(out)],
        check=True, capture_output=True)
    return out