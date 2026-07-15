# Week 3 Findings

## Geomean Performance vs O2

All methods were evaluated with an equal budget of 60 evaluations per benchmark.

| Method | Geomean vs O2 |
|----------|----------|
| Random Search | 0.595x |
| LLM One-Shot | 0.606x |
| Hill Climb | 0.611x |

### Observation

Hill Climb achieved the best overall performance, followed by LLM One-Shot and Random Search.

Ranking:

1. Hill Climb (0.611x)
2. LLM One-Shot (0.606x)
3. Random Search (0.595x)

This suggests that incorporating feedback from previous evaluations is more effective than both uninformed random exploration and one-shot LLM-generated optimization sequences.

---

## LLM vs Hill Climb

The LLM outperformed Hill Climb on only 1 out of 12 benchmarks.

| Benchmark | Hill Climb | LLM One-Shot |
|------------|------------|------------|
| jacobi-2d | 10,586,221 | 10,187,738 |

### Observation

Hill Climb produced better results on 11 out of 12 benchmarks.

The only benchmark where the LLM achieved a lower instruction count than Hill Climb was `jacobi-2d`.

`jacobi-2d` is a loop-heavy numerical kernel dominated by floating-point computations and regular memory access patterns. While this may indicate that LLM-generated optimization sequences can occasionally discover strong transformations for structured numerical workloads, a single benchmark is insufficient to establish a broader trend.

Overall, the results indicate that feedback-driven search is generally more reliable than one-shot LLM proposals.

---

## LLM Sequence Diversity

Five representative LLM-generated pass sequences were inspected manually:

1. early-cse, instcombine, reassociate, gvn, loop-simplify, indvars, loop-unroll, slp-vectorizer, tailcallelim, adce, dce, jump-threading
2. sroa, early-cse, instcombine, simplifycfg, reassociate, gvn, sccp, correlated-propagation, jump-threading, adce, dce, tailcallelim
3. early-cse, simplifycfg, loop-simplify, indvars, loop-unroll
4. sroa, early-cse, instcombine, simplifycfg, loop-simplify, loop-rotate, licm, indvars, loop-unroll, gvn, sccp, tailcallelim
5. sroa, early-cse, instcombine, simplifycfg, loop-simplify, loop-rotate, licm, indvars, loop-unroll, gvn, sccp, adce

### Observation

The generated sequences are not identical. The LLM consistently uses a common optimization template consisting of:

- Cleanup passes (sroa, early-cse, instcombine, simplifycfg)
- Loop canonicalization (loop-simplify, loop-rotate)
- Loop optimization (licm, indvars, loop-unroll)
- Redundancy elimination (gvn, sccp)
- Final cleanup (adce, dce, tailcallelim)

However, the ordering, subset selection, and inclusion of vectorization-related passes vary across proposals. This indicates that the LLM explores multiple optimization strategies rather than repeatedly emitting the same pipeline with cosmetic changes.

Overall, the proposal set exhibits moderate diversity: the model follows recognizable optimization patterns while still generating distinct candidate sequences.

---

## Sample Efficiency

To evaluate sample efficiency, Hill Climb's final best instruction count for each benchmark was used as the target. For every method, the earliest evaluation that achieved this target was recorded.

### Results

| Benchmark | Random Search | LLM One-Shot | Hill Climb |
|------------|------------|------------|------------|
| 2mm | Never | Never | 55 |
| 3mm | Never | Never | 48 |
| atax | Never | Never | 32 |
| bicg | Never | Never | 32 |
| correlation | Never | Never | 51 |
| covariance | Never | Never | 55 |
| gemm | Never | Never | 34 |
| gesummv | Never | Never | 30 |
| heat-3d | Never | Never | 60 |
| jacobi-2d | Never | 12 | 57 |
| mvt | Never | Never | 52 |
| seidel-2d | Never | Never | 23 |

### Observation

Random Search never matched Hill Climb's final best result on any benchmark within the 60-evaluation budget.

LLM One-Shot matched or exceeded Hill Climb's final result on only one benchmark (`jacobi-2d`), achieving the target after just 12 evaluations. On all remaining benchmarks, the LLM failed to reach Hill Climb's final best solution.

Hill Climb required between 23 and 60 evaluations to discover its strongest solutions, demonstrating the value of iterative feedback and local search.

### Conclusion

The sample-efficiency results highlight the trade-off between one-shot generation and feedback-driven optimization. The LLM can occasionally discover strong optimization sequences very quickly, as observed on `jacobi-2d`, but its performance is inconsistent. Hill Climb requires more evaluations but reliably improves candidate quality over time, ultimately producing the strongest search-based results across almost all benchmarks.