# Ablations

## A1: Feedback vs One-Shot

We compared the one-shot LLM proposer against the feedback-based LLM loop.

The feedback loop outperformed the one-shot approach on 7 out of 12 benchmarks. Examples include 3mm, atax, bicg, correlation, covariance, mvt, and seidel-2d.

However, the overall geomean speedup versus O2 was slightly lower for the feedback loop (0.600x) than for the one-shot approach (0.606x).

Interpretation:

The feedback mechanism clearly influenced the search process and helped on several individual benchmarks. However, the improvements were not consistent enough to improve overall geomean performance. This suggests that the measured feedback contains useful information, but the current prompting and history mechanism are not yet strong enough to consistently outperform the one-shot baseline.

---

## A2: History Size (h=8 vs h=2)

A reduced benchmark subset (gemm, atax, jacobi-2d, correlation, mvt) was used.

| Method | Geomean vs O2 |
|----------|----------|
| LLM Loop h=8 | 0.599x |
| LLM Loop h=2 | 0.607x |

Interpretation:

Reducing the history size from 8 to 2 had very little impact on performance. In fact, h=2 was slightly better on this benchmark subset.

This suggests that the model is not heavily relying on a long history of measured results. Most of the generated optimization sequences appear to come from the model's prior knowledge rather than extensive use of accumulated feedback.

---

## A3: Features vs No Features

A reduced benchmark subset (gemm, atax, jacobi-2d, correlation, mvt) was used.

| Method | Geomean vs O2 |
|----------|----------|
| LLM Loop h=8 | 0.599x |
| LLM No Features | 0.598x |

Interpretation:

Removing static IR features produced almost no change in performance.

This indicates that the current feature representation contributes little to proposal quality at this scale. The model appears capable of proposing similar optimization pipelines even without explicit program features.

---

## Summary

Across all ablations, performance differences were relatively small.

The strongest observation is that the LLM appears to rely primarily on learned compiler optimization priors. Neither longer measurement histories nor static IR features produced large improvements within the evaluation budget used in this study.

## Results

| Method | Geomean vs O2 |
|----------|----------|
| LLM OneShot | 0.608x |
| LLM Loop h=8 | 0.599x |
| LLM Loop h=2 | 0.607x |
| LLM No Features | 0.598x |