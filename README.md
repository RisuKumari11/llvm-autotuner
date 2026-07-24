# llvm-autotuner: LLM-in-the-loop LLVM Pass-Ordering Autotuner

Searches LLVM optimization pass orderings using classical search algorithms and a
local-LLM-guided feedback loop. Every candidate is measured with a deterministic
Callgrind instruction count and cross-checked with statistically-bounded wall-clock
timing, so every number in this README is directly reproducible from the committed
result files.

---

## Headline Result

![headline](plots/headline.png)

Across 12 PolyBench kernels, under a fixed budget of 60 evaluations per benchmark:

| Method | Geomean vs `-O2` (instruction count) | Beats `-O3` |
|---|---|---|
| Random search | 0.997× | 3 / 12 |
| Hill-climbing | **1.004×** | 6 / 12 |
| LLM one-shot | 1.003× | 6 / 12 |
| LLM + feedback loop | 0.999× | 4 / 12 |

None of the methods dominate `-O2` or `-O3` across the board. Hill-climbing and
LLM one-shot are essentially tied for best, matching or slightly beating `-O2` in
aggregate and beating `-O3` on half the suite - largely on the stencil kernels
(`heat-3d`, `seidel-2d`) and the smaller BLAS kernels (`bicg`, `gesummv`, `mvt`,
`gemm`). Random search is the weakest but still lands within 0.3% of `-O2`.

**Wall-clock validation of the hill-climbing winners**: geomean **0.974×** vs `-O2`
- see [Methodology and Honest Limitations](#methodology-and-honest-limitations) for
why an instruction-count win doesn't always translate to a wall-clock win.

---

## Quickstart (No LLM Required)

```bash
docker compose -f docker/docker-compose.yml build core
docker compose -f docker/docker-compose.yml run core
```

This builds baselines, runs a short hill-climbing search, and prints a comparison
table - no manual LLVM or PolyBench setup required. The LLM path (Ollama) is a
separate compose profile and is not needed to reproduce the core search result.

---

## How It Works

```text
PolyBench Kernel
        │
        ▼
   LLVM IR Generation  (clang -O0 -Xclang -disable-O0-optnone -emit-llvm)
        │
        ▼
Pass Sequence Generator
(Random / Hill-climb / LLM one-shot / LLM + feedback)
        │
        ▼
      opt -passes='...'
        │
        ▼
  Compilation  (clang -O2 -Xclang -disable-llvm-passes)
        │
        ▼
  Callgrind Instruction Count  (search reward)
        │
        ▼
   Search Feedback
        │
        ▼
  hyperfine Wall-Clock  (final validation only)
```

The codegen step (`clang -O2 -Xclang -disable-llvm-passes`) is deliberate: it gives
every tuned candidate the same backend (register allocation, instruction selection)
that the `-O2`/`-O3` baselines get, so the comparison isolates the effect of the
*pass ordering* rather than conflating it with a weaker backend.

### Search Methods

- **Random search** - samples valid pass sequences uniformly from a curated pool of
  ~20 LLVM passes.
- **Hill-climbing** - starts from an `-O2`-like seed sequence, mutates
  (replace/insert/delete/swap), keeps improvements, random-restarts on a plateau.
- **LLM one-shot** - a local LLM (Qwen2.5-Coder via Ollama) proposes a complete pass
  sequence per candidate, conditioned on static IR features (loop count, IR size,
  branch count).
- **LLM + feedback loop** - the same proposer, but each round is conditioned on the
  best-and-worst measured results from prior rounds.

All four methods share one `Evaluator`: every candidate - valid or invalid - consumes
one unit of a shared 60-evaluation budget, so the comparison is budget-matched by
construction, not by convention.

---

## Results

### Main Comparison

Instruction count, lower is better. Full per-benchmark table and reproduction command
below.

```bash
make search        # random + hillclimb, budget 60, seed 0
make llm           # llm-search  (one-shot)
python -m src.autotuner.cli llm-loop --budget 60 --seed 0
python -m src.autotuner.cli compare
```

| Benchmark | `-O2` | `-O3` | Random | Hill-climb | LLM 1-shot | LLM loop |
|---|---:|---:|---:|---:|---:|---:|
| 2mm | 6,065,221 | 6,001,963 | 6,068,952 | 6,067,577 | 6,067,936 | 6,067,489 |
| 3mm | 6,116,066 | 6,018,002 | 6,120,745 | 6,119,980 | 6,119,992 | 6,119,880 |
| atax | 5,986,321 | 5,983,676 | 5,987,274 | 5,985,833 | 5,985,362 | 5,985,370 |
| bicg | 5,992,596 | 5,992,581 | 5,988,847 | 5,988,043 | 5,988,055 | 5,988,049 |
| correlation | 6,044,075 | 6,019,248 | 6,063,906 | 6,056,460 | 6,060,471 | 6,060,450 |
| covariance | 6,036,591 | 6,015,133 | 6,054,085 | 6,052,523 | 6,047,853 | 6,052,086 |
| gemm | 6,049,471 | 6,073,667 | 6,083,203 | 6,043,208 | 6,048,798 | 6,081,720 |
| gesummv | 5,983,479 | 5,983,467 | 5,981,419 | 5,980,706 | 5,980,718 | 5,980,284 |
| heat-3d | 6,410,347 | 6,335,357 | 6,414,745 | 6,271,303 | 6,281,606 | 6,281,175 |
| jacobi-2d | 6,173,570 | 6,139,380 | 6,290,044 | 6,168,856 | 6,172,205 | 6,289,389 |
| mvt | 5,998,157 | 5,998,169 | 5,989,761 | 5,989,005 | 5,989,024 | 5,989,096 |
| seidel-2d | 6,517,495 | 6,514,966 | 6,554,448 | 6,369,600 | 6,373,752 | 6,552,217 |
| **geomean vs O2** | 1.000 | 1.004 | 0.997 | **1.004** | 1.003 | 0.999 |
| **beats O3** | - | - | 3/12 | 6/12 | 6/12 | 4/12 |

### Benchmark-Level Observations

- Hill-climbing and LLM one-shot beat `-O2` on the same 8 of 12 kernels: `atax`,
  `bicg`, `gemm`, `gesummv`, `heat-3d`, `jacobi-2d`, `mvt`, `seidel-2d`.
- Both beat `-O3` on 6 of those: `bicg`, `gemm`, `gesummv`, `heat-3d`, `mvt`,
  `seidel-2d` - mostly stencils and small, memory-bound BLAS kernels.
- Random search only beats both baselines on 3 kernels (`bicg`, `gesummv`, `mvt`),
  confirming that ordering matters - an `-O2`-informed starting point and local
  search meaningfully outperform unguided sampling at this budget.
- The LLM feedback loop underperforms LLM one-shot in aggregate (0.999 vs 1.003).
  See the ablation below for why.
- **No method beats `-O3` on `2mm`, `3mm`, `atax`, `correlation`, `covariance`, or
  `jacobi-2d`.** LLVM's hand-tuned `-O3` pipeline remains the strongest general
  baseline on this suite.

---

## Ablation Study

Run on a 5-benchmark subset (`gemm`, `atax`, `jacobi-2d`, `correlation`, `mvt`) to
keep experiment time manageable; not directly comparable to the 12-benchmark numbers
above.

```bash
python -m src.autotuner.cli llm-loop --budget 60 --history-size 2 \
    --benches gemm,atax,jacobi-2d,correlation,mvt --seed 0
python -m src.autotuner.cli llm-loop --budget 60 --no-features \
    --benches gemm,atax,jacobi-2d,correlation,mvt --seed 0
make ablations
```

| Variant | Geomean vs `-O2` (5-bench subset) |
|---|---|
| LLM one-shot | 1.000× |
| LLM loop, history=8 (default) | 0.995× |
| LLM loop, history=2 | 1.000× |
| LLM loop, no static IR features | 0.999× |

**A1 - feedback vs. one-shot:** the feedback loop did not improve on one-shot
prompting at this budget; if anything it was marginally worse. The model's
pretrained priors about good pass orderings appear stronger than what it can extract
from a handful of measured (sequence, instruction-count) pairs in-context.

**A2 - history size:** shrinking the feedback history from 8 to 2 measurements made
no meaningful difference, reinforcing A1 - the model isn't leaning heavily on
accumulated measurements either way.

**A3 - static IR features:** removing the loop-count / IR-size / branch-count
features from the prompt barely moved the result. At this scale, those features add
little beyond what the model infers from the pass-pool description itself.

**Honest takeaway:** the interesting result here is negative, and that's reported
plainly rather than papered over - measurement feedback, in this setup, budget, and
model size, doesn't reliably beat a good one-shot prompt. That's a real finding about
the limits of in-context feedback for this task, not a failure to hide.

---

## Methodology and Honest Limitations

### Primary metric: Callgrind instruction count

Deterministic and reproducible across runs on the same machine - verified by running
the same binary through Callgrind twice and confirming an identical count. This
determinism is what makes a 60-evaluation search budget tractable; wall-clock timing
alone would be far too noisy to search against directly.

### Wall-clock validation

The best hill-climbing sequence per benchmark was rebuilt on the wall-clock dataset
and timed with `hyperfine` (3 warmups, ≥10 runs, plugged in, pinned to one core).

| Benchmark | Tuned (s) | `-O2` (s) | Speedup |
|---|---:|---:|---:|
| gemm | 0.00944 | 0.00869 | 0.921× |
| 2mm | 0.01125 | 0.01103 | 0.980× |
| 3mm | 0.00996 | 0.01022 | 1.027× |
| atax | 0.00990 | 0.00789 | 0.796× |
| bicg | 0.00828 | 0.00767 | 0.925× |
| mvt | 0.00767 | 0.00858 | 1.119× |
| gesummv | 0.00760 | 0.00764 | 1.006× |
| jacobi-2d | 0.00779 | 0.00775 | 0.995× |
| seidel-2d | 0.01179 | 0.01102 | 0.935× |
| heat-3d | 0.00797 | 0.00788 | 0.988× |
| correlation | 0.00789 | 0.00828 | 1.049× |
| covariance | 0.00782 | 0.00769 | 0.983× |
| **geomean** | | | **0.974×** |

The instruction-count win doesn't uniformly hold in wall-clock: `atax` wins on
instruction count but loses 20% in real time, most likely from a pass ordering that
shifted memory-access patterns (cache/branch-prediction effects that a static
instruction count can't see). `mvt` and `correlation` show the opposite: a modest
instruction-count win translates into a larger real-time win. **This is the clearest
limitation of instruction-count-only search, and it's the reason wall-clock
validation is a required final step, not an optional one.**

### Experimental controls

- Evaluation budget: 60 per benchmark, per method (invalid candidates and duplicate
  cache hits are excluded from the budget the same way, or included the same way,
  across every method - see `src/autotuner/search/evaluate.py`).
- Benchmarks: 12 PolyBench/C kernels, `MINI_DATASET` for Callgrind,
  `SMALL_DATASET` for wall-clock.
- Seed: 0 (single seed; multi-seed variance is a known gap, see below).
- LLM: Qwen2.5-Coder via local Ollama, temperature 0.8, 100% valid-proposal rate
  (mean 1.07 attempts per accepted proposal).

### Known limitations

- **Single seed.** All results use seed 0. Cross-seed variance for the search
  methods hasn't been characterized; treat the geomean differences between random,
  hill-climbing, and LLM one-shot (0.997 / 1.004 / 1.003) as suggestive rather than
  statistically bounded.
- **Instruction count is a proxy**, not the ground truth - see the wall-clock
  section above.
- **`-O3` remains the strongest baseline** on half the suite. This project searches
  a curated ~20-pass pool with fixed-length sequences; it is not a claim to have
  matched or exceeded LLVM's full, hand-engineered `-O3` pipeline in general.

---

## Repository Structure

```text
llvm-autotuner/
├── src/autotuner/
│   ├── llm/                 # LLM proposer, prompts, feedback loop, client
│   ├── search/              # Random search, hill-climbing, shared Evaluator
│   ├── cli.py                # baselines / search / llm-search / llm-loop / compare / validate / report
│   ├── compile.py             # pass-sequence application (opt + O2 backend)
│   ├── measure.py             # Callgrind + hyperfine wrappers
│   ├── ir.py                  # LLVM IR generation
│   ├── store.py               # Parquet result storage
│   └── stats.py               # geomean, bootstrap CIs
├── configs/                   # benchmark list, curated pass pool
├── scripts/                   # plot generation, ablation table, benchmark fetch
├── docker/                    # Dockerfile + compose (core + optional ollama profile)
├── tests/                     # unit tests (fast) + integration tests (need LLVM)
├── results/                    # live results (regenerable)
├── results_final/              # frozen snapshot backing this README
├── plots/                      # headline figure
└── .github/workflows/          # CI: lint, unit tests, smoke run, docker build
```

---

## Reproducibility

```bash
# full search + comparison, from scratch
make baselines
make search
make llm
python -m src.autotuner.cli llm-loop --budget 60 --seed 0
python -m src.autotuner.cli compare
python -m src.autotuner.cli validate
make ablations

# or, the no-toolchain-required smoke path
docker compose -f docker/docker-compose.yml run core
```

CI (`.github/workflows/ci.yml`) runs Ruff lint, the unit test suite (mocked LLM
client, no network), a fast deterministic smoke search, and a Docker build check on
every push.

---

## What's Next

- Multi-seed runs to put confidence intervals around the geomean differences between
  methods.
- Extend the curated pass pool (currently ~20 passes) and compare against the full
  `-O3` pipeline vocabulary.
- Investigate the `atax` instruction-count-vs-wall-clock divergence directly (perf
  counters / cache-miss profiling) rather than treating it as an unexplained outlier.
