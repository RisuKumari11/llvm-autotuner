"""Apply a pass sequence to linked bitcode and produce a binary."""
import subprocess
from pathlib import Path

from .config import LOOP_PASSES

OPT = "opt"
CLANG = "clang"

class InvalidCandidate(Exception):
    """Pass sequence failed to compile. Treat as invalid, not fatal."""

def build_pass_string(passes: list[str]) -> str:
    """Group consecutive loop passes into loop-mssa(...) adaptors."""
    out, i = [], 0
    while i < len(passes):
        if passes[i] in LOOP_PASSES:
            j = i
            while j < len(passes) and passes[j] in LOOP_PASSES:
                j += 1
            out.append(f"loop-mssa({','.join(passes[i:j])})")
            i = j
        else:
            out.append(passes[i])
            i += 1
    return ",".join(out)

def compile_with_passes(linked_bc: Path, passes: list[str], out_bin: Path,
                        timeout: int = 120) -> Path:
    tuned = out_bin.with_suffix(".bc")
    pass_str = build_pass_string(passes)
    try:
        subprocess.run([OPT, f"-passes={pass_str}", str(linked_bc), "-o", str(tuned)],
                       check=True, capture_output=True, timeout=timeout)
        subprocess.run(
            [
                CLANG,
                "-O2",
                "-Xclang",
                "-disable-llvm-passes",
                str(tuned),
                "-lm",
                "-o",
                str(out_bin),
            ],
            check=True,
            capture_output=True,
            timeout=timeout,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        stderr = getattr(e, "stderr", b"") or b""
        raise InvalidCandidate(f"passes={pass_str}: {stderr.decode()[:300]}") from e
    return out_bin