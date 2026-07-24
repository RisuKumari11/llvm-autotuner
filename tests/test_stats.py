from src.autotuner.stats import geomean, median_ci


def test_geomean():
    assert abs(geomean([1, 4]) - 2.0) < 1e-9


def test_median_ci_contains_median():
    med, lo, hi = median_ci([1.0, 1.1, 0.9, 1.05, 0.95] * 4)
    assert lo <= med <= hi