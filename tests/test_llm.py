import pytest

from src.autotuner.llm.parse import parse_proposal
from src.autotuner.llm.prompts import POOL, proposal_prompt


def test_parse_clean_json():
    p = parse_proposal('{"reasoning": "x", "passes": ["sroa", "gvn", "instcombine", "adce"]}')
    assert p.passes[0] == "sroa"

def test_parse_with_markdown_fence():
    txt = 'Here you go:\n```json\n{"reasoning":"r","passes":["sroa","gvn","adce","dce"]}\n```'
    assert parse_proposal(txt).passes == ["sroa", "gvn", "adce", "dce"]

def test_unknown_pass_rejected():
    with pytest.raises(ValueError):
        parse_proposal('{"reasoning":"r","passes":["sroa","made-up-pass","gvn","adce"]}')

def test_too_short_rejected():
    with pytest.raises(ValueError):
        parse_proposal('{"reasoning":"r","passes":["sroa"]}')

def test_prompt_contains_pool_and_features():
    msgs = proposal_prompt("gemm", {"num_loops": 3})
    text = msgs[-1]["content"]
    assert all(p in text for p in POOL) and "num_loops" in text

def test_history_appended():
    msgs = proposal_prompt("gemm", {}, history=[{"passes": "sroa,gvn", "instr": 123}])
    assert "Previously measured" in msgs[-1]["content"]

def test_agent_retries(monkeypatch):
    from src.autotuner.llm import agent
    calls = {"n": 0}
    def fake_chat(msgs, **kw):
        calls["n"] += 1
        if calls["n"] < 3:
            return "garbage not json"
        return '{"reasoning":"r","passes":["sroa","gvn","instcombine","adce"]}'
    monkeypatch.setattr(agent, "chat", fake_chat)
    seq, attempts = agent.propose("gemm", {})
    assert seq == ["sroa", "gvn", "instcombine", "adce"] and attempts == 3