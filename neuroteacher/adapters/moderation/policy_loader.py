from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple, Pattern
import os, re, yaml

@dataclass
class SafetyPolicy:
    model: Optional[str]
    danger_real_world_markers: List[Pattern]
    replace_terms: List[Tuple[Pattern, str]]
    blocked_input: str

    @classmethod
    def load(cls, path: Optional[str] = None) -> "SafetyPolicy":
        path = path or os.environ.get("SAFETY_POLICY_PATH") or "safety_policy.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        model = None
        try:
            model = data["thresholds"]["moderation"]["model"]
        except Exception:
            model = None
        markers = [re.compile(p, flags=re.I) for p in (data.get("danger", {}).get("real_world_markers", []) or [])]
        replaces = []
        for rule in (data.get("replace", {}).get("terms", []) or []):
            frm = rule.get("from"); to = rule.get("to","")
            if frm: replaces.append((re.compile(frm, flags=re.I), to))
        blocked = data.get("responses", {}).get("blocked_input", "Запрос заблокирован политикой безопасности.")
        return cls(model=model, danger_real_world_markers=markers, replace_terms=replaces, blocked_input=blocked)

    def sanitize(self, text: str) -> str:
        for pat, rep in self.replace_terms:
            text = pat.sub(rep, text)
        return text

    def has_danger_markers(self, text: str) -> bool:
        return any(p.search(text) for p in self.danger_real_world_markers)
