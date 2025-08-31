import re, requests
from typing import List
from neuroteacher.core.types import Doc
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except Exception:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

class GDocsLoader:
    def __init__(self, url: str, chunk_size: int = 800, chunk_overlap: int = 100, timeout: int = 30):
        self.url = url
        self.timeout = timeout
        self._splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    def _extract_id(self) -> str:
        m = re.search(r"/document/d/([a-zA-Z0-9\-_]+)", self.url)
        if not m: raise ValueError("Неверный Google Docs URL: " + self.url)
        return m.group(1)
    def _download_txt(self, doc_id: str) -> str:
        resp = requests.get(f"https://docs.google.com/document/d/{doc_id}/export?format=txt", timeout=self.timeout, allow_redirects=True,
                            headers={"User-Agent": "Mozilla/5.0"})
        if "accounts.google.com" in resp.url: raise PermissionError("Документ приватный или недоступен анонимно.")
        resp.raise_for_status(); return resp.text
    def load(self, course_key: str) -> List[Doc]:
        doc_id = self._extract_id(); text = self._download_txt(doc_id); chunks = self._splitter.split_text(text)
        return [Doc(page_content=part, metadata={"course": course_key, "doc_id": f"{doc_id}_{i}", "source": self.url, "preview": part[:120]})
                for i, part in enumerate(chunks, 1)]
