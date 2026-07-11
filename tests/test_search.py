import random
from src.autotuner.search.random_search import sample_sequence, POOL
from src.autotuner.search.hillclimb import mutate, O2_LIKE
from src.autotuner.compile import build_pass_string

def test_sample_in_pool_and_length():
    rng = random.Random(0)
    for _ in range(50):
        s = sample_sequence(rng)
        assert 12 <= len(s) <= 24 and all(p in POOL for p in s)

def test_sampling_deterministic_per_seed():
    a = [sample_sequence(random.Random(7)) for _ in range(5)]
    b = [sample_sequence(random.Random(7)) for _ in range(5)]
    assert a == b

def test_mutate_stays_valid():
    rng = random.Random(1)
    s = list(O2_LIKE)
    for _ in range(100):
        s = mutate(s, rng)
        assert len(s) >= 4 and all(p in POOL for p in s)
        build_pass_string(s)   # must never raise