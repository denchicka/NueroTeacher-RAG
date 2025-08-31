from __future__ import annotations
from typing import Dict, Any, List
from neuroteacher.adapters.moderation.policy_loader import SafetyPolicy
from neuroteacher.adapters.moderation.moderator import Moderator
from neuroteacher.core.types import Doc

class SafetyService:
    def __init__(self, policy_path: str | None = None):
        self.policy = SafetyPolicy.load(policy_path)
        self.moderator = Moderator(self.policy)

    def check_input(self, text: str) -> Dict[str, Any]:
        return self.moderator.moderate(text)

    def sanitize_docs(self, docs: List[Doc]) -> List[Doc]:
        return [Doc(page_content=self.policy.sanitize(d.page_content), metadata=d.metadata) for d in docs]
