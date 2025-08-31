from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class Doc:
    page_content: str
    metadata: Dict[str, Any]
