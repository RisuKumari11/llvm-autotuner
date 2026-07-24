"""Cheap static features of a benchmark's IR, for prompting."""
import re
import subprocess
from pathlib import Path


def ir_features(linked_bc: Path) -> dict:
    # human-readable IR
    ll = subprocess.run(["llvm-dis", str(linked_bc), "-o", "-"],
                        check=True, capture_output=True, text=True).stdout
    # loop count via opt's loop printer
    loops = subprocess.run(
        ["opt", "-passes=print<loops>", "-disable-output", str(linked_bc)],
        capture_output=True, text=True, check=False,).stderr
    return {
        "ir_lines": ll.count("\n"),
        "num_functions": len(re.findall(r"^define ", ll, re.MULTILINE)),
        "num_loops": loops.count("Loop at depth"),
        "max_loop_depth": max([int(d) for d in
                               re.findall(r"Loop at depth (\d+)", loops)] or [0]),
        "has_fp": (" double" in ll or " float" in ll),
        "num_geps": ll.count("getelementptr"),   # rough memory-access proxy
        "num_branches": ll.count("br "),
    }