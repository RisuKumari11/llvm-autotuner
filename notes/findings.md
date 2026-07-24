# Findings

## Week 1 – Baseline Measurements

### Baseline instruction counts

The LLVM optimization levels were evaluated on the selected PolyBench benchmarks to establish reference instruction counts.

- `-O2` consistently produced substantial reductions over `-O0`.
- `-O3` provided modest improvements over `-O2` on several benchmarks but was not universally superior.

These baselines serve as the reference for all subsequent search methods.

---

## Week 2 – Search Strategy Comparison

### Geometric Mean Improvement (vs `-O2`)

All methods were evaluated under the same search budget.

| Method | Geomean vs `-O2` |
|---------|-----------------:|
| Random Search | **0.997×** |
| Hill Climb | **1.003×** |
| LLM One-Shot | **1.003×** |

### Observations

- Hill Climb and LLM One-Shot achieved essentially identical geometric-mean performance.
- Random Search performed slightly worse than the other two methods.
- Under the evaluated budget, no clear overall winner emerged between Hill Climb and LLM One-Shot.

---

### Benchmarks where LLM Outperformed Hill Climb

Comparing the final best instruction counts:

| Benchmark | Better Method |
|-----------|---------------|
| atax | LLM One-Shot |
| covariance | LLM One-Shot |

Across the remaining benchmarks, Hill Climb achieved lower instruction counts.

Both `atax` and `covariance` belong to the PolyBench data-mining kernels and consist primarily of dense floating-point computations. While this suggests the LLM-generated pass sequences may be particularly effective for these workloads, the sample size is too small to draw broader conclusions.

---

### LLM Pass Sequence Diversity

Inspection of representative LLM-generated pass sequences showed that:

- Most sequences shared a common optimization structure.
- Differences were primarily the ordering of several passes or the inclusion/removal of a small number of transformations.
- The LLM generally produced conservative variations rather than completely different optimization pipelines.

Overall, the generated sequences exhibited limited diversity.

---

### Sample Efficiency

Sample efficiency was measured as the number of evaluations required for a method's **running best instruction count to match or outperform Hill Climb's final best instruction count** for each benchmark.

| Benchmark | Random Search | LLM One-Shot | Hill Climb |
|-----------|---------------|--------------|-----------:|
| 2mm | Never | Never | 26 |
| 3mm | Never | Never | 24 |
| atax | Never | 4 | 17 |
| bicg | Never | Never | 38 |
| correlation | Never | Never | 41 |
| covariance | Never | 3 | 13 |
| gemm | Never | Never | 58 |
| gesummv | Never | Never | 17 |
| heat-3d | Never | Never | 58 |
| jacobi-2d | Never | Never | 22 |
| mvt | Never | Never | 10 |
| seidel-2d | Never | Never | 25 |

### Observations

- Hill Climb reached its own final solution on every benchmark.
- LLM One-Shot matched or exceeded Hill Climb's final instruction count on two benchmarks (`atax` and `covariance`), doing so in only 4 and 3 evaluations respectively.
- Random Search never reached Hill Climb's final quality within the search budget.
- Although Hill Climb and LLM One-Shot achieved nearly identical geometric-mean performance overall, they typically converged to different local optima.

---

## Week 3 – Feedback Loop

A feedback-based LLM optimization loop was evaluated against the original one-shot prompting strategy.

### Geometric Mean (vs `-O2`)

| Method | Geomean vs `-O2` |
|---------|-----------------:|
| LLM One-Shot | **1.003×** |
| LLM Feedback Loop | **0.999×** |

### Observations

- The feedback loop did not improve overall optimization quality.
- Under the evaluated search budget, iterative prompting offered no measurable advantage over one-shot generation.

---

### Proposal Quality

- Valid proposal rate: **100%**
- Mean attempts per accepted proposal: **1.07**

The prompt consistently generated syntactically valid LLVM optimization pipelines, requiring very few retries.

---

### Benchmarks Beating `-O3`

| Method | Benchmarks Better than `-O3` |
|---------|-----------------------------:|
| Hill Climb | 6 / 12 |
| LLM One-Shot | 6 / 12 |
| LLM Feedback Loop | 4 / 12 |

Hill Climb and LLM One-Shot both outperformed LLVM's `-O3` optimization level on six benchmarks, while the feedback loop achieved this on four benchmarks.

---

## Week 4 – Ablation Study

To understand which components contributed to feedback-loop performance, two ablations were evaluated.

| Variant | Geomean vs `-O2` |
|---------|-----------------:|
| One-Shot | **1.000×** |
| Loop (History = 8) | **0.995×** |
| Loop (History = 2) | **1.000x** |
| Loop (No Static Features) | **0.999×** |

### Observations

- Shortening the optimization history produced almost no change in performance.
- Removing LLVM IR static features also had minimal impact.
- Under the evaluated search budget and benchmark subset, neither longer optimization histories nor static program features produced measurable improvements.
- These results suggest that the current prompting strategy does not effectively exploit the additional contextual information, although richer program representations or stronger feedback mechanisms may improve performance in future work.

---

## Overall Conclusions

- Hill Climb and LLM One-Shot achieved comparable overall optimization quality.
- Random Search was consistently less effective.
- The LLM generated mostly conservative variations of similar optimization pipelines.
- Feedback-based prompting did not improve optimization quality over one-shot prompting.
- The LLM was able to outperform Hill Climb on two benchmarks (`atax` and `covariance`), indicating that LLM-guided search can occasionally discover better optimization pipelines than deterministic local search.
- Future work should investigate richer program representations, stronger search strategies, and more informative feedback signals to better exploit LLM reasoning during compiler optimization.