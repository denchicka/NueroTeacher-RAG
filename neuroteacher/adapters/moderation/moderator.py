from __future__ import annotations
from typing import Any, Dict
from .policy_loader import SafetyPolicy

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

class Moderator:
    def __init__(self, policy: SafetyPolicy):
        self.policy = policy
        self._client = OpenAI() if (OpenAI is not None and policy.model) else None

    def moderate(self, text: str) -> Dict[str, Any]:
        sanitized = self.policy.sanitize(text)
        flagged_policy = self.policy.has_danger_markers(sanitized)
        flagged_model = False
        model_flags: Dict[str, Any] = {}
        if self._client:
            try:
                resp = self._client.moderations.create(model=self.policy.model, input=sanitized)
                result = resp.results[0] if hasattr(resp, "results") else None
                if result:
                    flagged_model = bool(getattr(result, "flagged", False))
                    model_flags = getattr(result, "categories", {}) or {}
            except Exception:
                flagged_model = False
        allowed = not (flagged_policy or flagged_model)
        reasons = []
        if flagged_policy: reasons.append("policy_markers")
        if flagged_model: reasons.append("model_moderation")
        return {
            "allowed": allowed,
            "flagged": (flagged_policy or flagged_model),
            "reasons": reasons,
            "sanitized": sanitized,
            "model_flags": model_flags,
            "blocked_message": self.policy.blocked_input
        }
