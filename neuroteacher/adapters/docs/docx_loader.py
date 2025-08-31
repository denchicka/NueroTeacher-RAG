from typing import List
from docx import Document as DocxDocument
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except Exception:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
from neuroteacher.core.types import Doc

class DocxLoader:
    def __init__(self, path: str, chunk_size: int = 500, chunk_overlap: int = 50):
        self.path = path; self.chunk_size = chunk_size; self.chunk_overlap = chunk_overlap
    def _split_text(self, text: str) -> List[str]:
        return RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap).split_text(text)
    def load(self, course_key: str) -> List[Doc]:
        doc = DocxDocument(self.path); current_h1 = current_h2 = current_h3 = ""; buffer: List[str] = []; output: List[Doc] = []
        def flush_buffer():
            nonlocal buffer, output, current_h1, current_h2, current_h3
            if not buffer: return
            raw = "\n".join(buffer)
            for i, chunk in enumerate(self._split_text(raw), 1):
                output.append(Doc(page_content=chunk, metadata={"course": course_key, "source": self.path, "h1": current_h1, "h2": current_h2, "h3": current_h3, "chunk_id": i}))
            buffer.clear()
        for para in doc.paragraphs:
            style = para.style.name if para.style else ""; text = (para.text or "").strip()
            if not text: continue
            if style.startswith("Heading 1") or style.startswith("Заголовок 1"): flush_buffer(); current_h1, current_h2, current_h3 = text, "", ""
            elif style.startswith("Heading 2") or style.startswith("Заголовок 2"): flush_buffer(); current_h2, current_h3 = text, ""
            elif style.startswith("Heading 3") or style.startswith("Заголовок 3"): flush_buffer(); current_h3 = text
            else: buffer.append(text)
        flush_buffer(); return output
