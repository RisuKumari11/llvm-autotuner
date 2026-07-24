"""Emit linked, optimizable LLVM bitcode for a PolyBench kernel."""
import subprocess
from pathlib import Path

from .config import POLYBENCH

CLANG = "clang"
LLVM_LINK = "llvm-link"   # change to llvm-link-18 etc. if needed

def emit_linked_bc(bench_path: str, dataset: str, workdir: Path) -> Path:
    """Compile kernel + polybench.c to one linked .bc at -O0 (optnone disabled)."""
    workdir.mkdir(parents=True, exist_ok=True)
    kdir = POLYBENCH / bench_path
    kernel_c = next(kdir.glob("*.c"))
    common = [
        CLANG, "-O0", "-Xclang", "-disable-O0-optnone", "-emit-llvm", "-c",
        "-I", str(POLYBENCH / "utilities"), "-I", str(kdir),
        f"-D{dataset}", "-DPOLYBENCH_TIME",
    ]
    kbc = workdir / "kernel.bc"
    pbc = workdir / "polybench.bc"
    linked = workdir / "linked.bc"
    subprocess.run(common + [str(kernel_c), "-o", str(kbc)], check=True, capture_output=True)
    subprocess.run(common + [str(POLYBENCH / "utilities" / "polybench.c"), "-o", str(pbc)],
                   check=True, capture_output=True)
    subprocess.run([LLVM_LINK, str(kbc), str(pbc), "-o", str(linked)],
                   check=True, capture_output=True)
    return linked