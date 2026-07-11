"""One canonical way to score a pass sequence on a benchmark."""
from dataclasses import dataclass, field
from pathlib import Path

from ..ir import emit_linked_bc
from ..compile import compile_with_passes, InvalidCandidate
from ..measure import instruction_count
from ..config import BENCH_CFG

WORK = Path("/tmp/autotuner/search")

@dataclass
class Evaluator:
    """Caches the linked .bc per benchmark and scores candidates."""
    bench_name: str
    bench_path: str
    dataset: str = ""
    _linked: Path | None = field(default=None, repr=False)
    evals: int = 0          # budget counter: every attempt counts, valid or not
    cache: dict = field(default_factory=dict)

    def __post_init__(self):
        self.dataset = self.dataset or BENCH_CFG["dataset_callgrind"]
        wd = WORK / self.bench_name
        self._linked = emit_linked_bc(self.bench_path, self.dataset, wd)

    def score(self, passes: list[str]) -> int | None:
        """Instruction count (lower better). None if the candidate is invalid."""
        key = tuple(passes)
        if key in self.cache:
            return self.cache[key]
        self.evals += 1
        out = WORK / self.bench_name / f"cand_{self.evals}"
        try:
            binary = compile_with_passes(self._linked, passes, out)
            val = instruction_count(binary)
        except InvalidCandidate:
            val = None
        self.cache[key] = val
        # clean up binaries so /tmp doesn't balloon
        out.unlink(missing_ok=True)
        out.with_suffix(".bc").unlink(missing_ok=True)
        return val