"""Parse and validate LLM proposals."""
import json
import re
from pydantic import BaseModel, field_validator
from .prompts import POOL

class Proposal(BaseModel):
    reasoning: str = ""
    passes: list[str]

    @field_validator("passes")
    @classmethod
    def valid_passes(cls, v):
        if not (4 <= len(v) <= 32):
            raise ValueError(f"length {len(v)} out of range")
        bad = [p for p in v if p not in POOL]
        if bad:
            raise ValueError(f"unknown passes: {bad}")
        return v

def extract_json(text: str) -> dict:
    """Tolerate markdown fences and leading prose."""
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("no JSON object in response")
    return json.loads(m.group(0))

def parse_proposal(text: str) -> Proposal:
    return Proposal(**extract_json(text))