from typing import List
from neuroteacher.adapters.docs.docx_loader import DocxLoader
from neuroteacher.adapters.docs.gdocs_loader import GDocsLoader
from neuroteacher.core.types import Doc
from neuroteacher.services.safety_service import SafetyService

class IndexingService:
    def __init__(self, chunk_size: int = 500, overlap: int = 50, policy_path: str | None = None):
        self.chunk_size = chunk_size; self.overlap = overlap
        self.safety = SafetyService(policy_path)

    def load_docx(self, path: str, course_key: str) -> List[Doc]:
        docs = DocxLoader(path, chunk_size=self.chunk_size, chunk_overlap=self.overlap).load(course_key)
        return self.safety.sanitize_docs(docs)

    def load_gdocs(self, url: str, course_key: str) -> List[Doc]:
        docs = GDocsLoader(url, chunk_size=max(self.chunk_size, 800), chunk_overlap=100).load(course_key)
        return self.safety.sanitize_docs(docs)
