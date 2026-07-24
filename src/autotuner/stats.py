import numpy as np
from scipy import stats as st


def geomean(x) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.exp(np.log(x).mean()))

def median_ci(samples, confidence=0.95, n_boot=5000, seed=0):
    """Bootstrap CI on the median."""
    rng = np.random.default_rng(seed)
    s = np.asarray(samples, dtype=float)
    meds = np.median(rng.choice(s, size=(n_boot, len(s)), replace=True), axis=1)
    lo, hi = np.percentile(meds, [(1-confidence)/2*100, (1+confidence)/2*100])
    return float(np.median(s)), float(lo), float(hi)

def faster_than(a_times, b_times, alpha=0.05) -> bool:
    """Is A significantly faster than B? Mann-Whitney U, one-sided."""
    _, p = st.mannwhitneyu(a_times, b_times, alternative="less")
    return p < alpha