from typing import Optional
from neuroteacher.core.contracts import VectorStore, Retriever
from neuroteacher.core.types import Doc
try:
    from langchain_chroma import Chroma
except Exception:
    try:
        from langchain_community.vectorstores import Chroma
    except Exception:
        Chroma = None

class _RetrieverAdapter(Retriever):
    def __init__(self, lc_retriever):
        self._r = lc_retriever
    def invoke(self, query: str):
        # Try modern LangChain retriever API
        if hasattr(self._r, "invoke"):
            return self._r.invoke(query)
        # Fallback to classic API
        if hasattr(self._r, "get_relevant_documents"):
            return self._r.get_relevant_documents(query)
        raise AttributeError("Underlying retriever has no invoke/get_relevant_documents")
    def get_relevant_documents(self, query: str):
        return self.invoke(query)

class ChromaVectorStore(VectorStore):
    def __init__(self, embeddings_adapter, persist_directory: Optional[str] = None):
        if Chroma is None: raise RuntimeError("Установите langchain-chroma")
        self._emb = getattr(embeddings_adapter, "_emb", None); self._persist = persist_directory; self._vs = None
    def add(self, docs: list[Doc]):
        texts = [d.page_content for d in docs]; metas = [d.metadata for d in docs]
        if self._vs is None: self._vs = Chroma(embedding_function=self._emb, persist_directory=self._persist)
        self._vs.add_texts(texts=texts, metadatas=metas)
    def as_retriever(self, **kwargs) -> Retriever:
        k = kwargs.get("k", 5)
        if self._vs is None: self._vs = Chroma(embedding_function=self._emb, persist_directory=self._persist)
        return _RetrieverAdapter(self._vs.as_retriever(search_kwargs={"k": k}))
