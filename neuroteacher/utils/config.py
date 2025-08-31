from __future__ import annotations
import tomllib, pathlib

def load_models_config(path: str | None = None) -> dict:
    p = pathlib.Path(path or "config/models.toml")
    if not p.exists():
        return {"providers": {"openai": {"models": ["gpt-4o-mini"]}, "gigachat": {"models":["gigachat-2-lite"]}}}
    with p.open("rb") as f:
        data = tomllib.load(f)
    return data or {}
