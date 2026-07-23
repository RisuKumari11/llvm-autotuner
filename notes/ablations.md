# Ablation Study

## Experimental Setup

To understand which components of the LLM-guided search contribute to optimization quality, we performed three ablation studies on a reduced benchmark suite consisting of five representative PolyBench kernels:

- gemm
- atax
- jacobi-2d
- correlation
- mvt

Each experiment used the same search budget of **60 evaluations per benchmark**. The reduced benchmark set was chosen to keep the total runtime manageable while still covering a diverse collection of linear algebra and stencil workloads.

> **Note:** The geomean values reported in this section are computed **only over the five-benchmark ablation subset** and are therefore **not directly comparable** to the geomean values reported in the main evaluation, which uses all twelve benchmarks.

---

## Results

| Variant | Geomean Speedup vs O2 |
|:--------|----------------------:|
| LLM One-Shot | **1.000×** |
| LLM Loop (History = 8) | **0.995×** |
| LLM Loop (History = 2) | **0.999×** |
| LLM Loop (No IR Features) | **0.999×** |

---

## A1. Feedback vs. One-Shot Search

### Motivation

The feedback loop is intended to improve search quality by allowing the LLM to observe previously evaluated optimization sequences and propose improved candidates in subsequent rounds. This experiment evaluates whether iterative feedback provides a measurable advantage over generating all optimization sequences independently.

### Method

- **LLM One-Shot:** Each proposal is generated independently without knowledge of previous evaluations.
- **LLM Loop (History = 8):** The LLM receives the best previously evaluated optimization sequences together with one poor-performing sequence before generating the next batch of proposals.

### Observation

On the selected benchmark subset, the feedback-loop variant achieved a geometric mean speedup of **0.995×** compared to **1.000×** for the one-shot baseline.

### Interpretation

Within the available evaluation budget, iterative feedback did **not** improve optimization quality. The measured optimization history was insufficient to consistently guide the model toward better optimization sequences than those produced directly from its pretrained knowledge.

---

## A2. Effect of Feedback History Size

### Motivation

The previous experiment only establishes whether feedback is useful. This ablation investigates whether providing **more optimization history** improves proposal quality.

### Method

Two feedback-loop configurations were compared:

- **History = 8** (default)
- **History = 2**

Both experiments used identical search budgets and benchmark sets.

### Observation

| History Size | Geomean Speedup vs O2 |
|--------------|----------------------:|
| 8 | **0.995×** |
| 2 | **0.999×** |

The difference between the two configurations is very small.

### Interpretation

Reducing the amount of optimization history from eight previous measurements to two did not significantly change the optimization outcome. This suggests that, at the current search budget and benchmark scale, the LLM relies primarily on its pretrained optimization priors rather than extracting substantial additional benefit from longer optimization histories.

---

## A3. Effect of Static LLVM IR Features

### Motivation

The proposal prompt includes a static feature vector extracted from the LLVM IR. This experiment evaluates whether these program features meaningfully influence the optimization sequences proposed by the LLM.

### Method

Two configurations were compared:

- Standard LLM Loop using extracted LLVM IR features.
- LLM Loop with the feature dictionary replaced by an empty dictionary (`{}`).

All other settings remained unchanged.

### Observation

| Configuration | Geomean Speedup vs O2 |
|---------------|----------------------:|
| With IR Features | **0.995×** |
| Without IR Features | **0.999×** |

The difference between the two configurations is negligible.

### Interpretation

Static LLVM IR features did **not** measurably improve optimization quality at this evaluation scale. This suggests that the feature representation used in the prompt provided little additional information beyond what the model already inferred from the optimization task itself.

This is a valid experimental outcome rather than a negative result. It indicates that richer program representations or stronger integration between static analysis and prompting may be required for feature-based conditioning to become effective.

---

## Summary

Across all three ablation studies, the proposed modifications produced only minor differences in optimization quality.

The experiments indicate that:

- Iterative feedback did not provide a measurable advantage over one-shot prompting.
- Increasing the feedback history from two to eight previous evaluations produced little additional benefit.
- Static LLVM IR features did not measurably improve optimization quality at the evaluated scale.

Overall, these results suggest that, under the current evaluation budget and benchmark suite, the LLM's optimization proposals are dominated by its pretrained optimization knowledge rather than by accumulated optimization history or the static LLVM IR feature vector. These findings help clarify the current limitations of LLM-guided compiler autotuning and motivate future work on stronger program representations and more informative feedback mechanisms.