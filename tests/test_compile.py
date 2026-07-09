import pytest
from src.autotuner.compile import build_pass_string, compile_with_passes, InvalidCandidate
from src.autotuner.ir import emit_linked_bc

def test_loop_pass_wrapping():
    s = build_pass_string(["sroa", "loop-rotate", "licm", "gvn"])
    assert s == "sroa,loop-mssa(loop-rotate,licm),gvn"

def test_function_passes_untouched():
    assert build_pass_string(["sroa", "gvn"]) == "sroa,gvn"

def test_invalid_pass_raises(tmp_path):
    bc = emit_linked_bc("linear-algebra/blas/gemm", "MINI_DATASET", tmp_path)
    with pytest.raises(InvalidCandidate):
        compile_with_passes(bc, ["not-a-real-pass"], tmp_path / "bin")

def test_valid_sequence_builds(tmp_path):
    bc = emit_linked_bc("linear-algebra/blas/gemm", "MINI_DATASET", tmp_path)
    b = compile_with_passes(bc, ["sroa", "instcombine", "gvn"], tmp_path / "bin")
    assert b.exists()