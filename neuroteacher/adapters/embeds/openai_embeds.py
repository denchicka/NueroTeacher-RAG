from neuroteacher.core.contracts import Embeddings
try:
    from langchain_openai import OpenAIEmbeddings
except Exception:
    OpenAIEmbeddings = None

class OpenAIEmbeddingsAdapter(Embeddings):
    def __init__(self, model: str = "text-embedding-3-small"):
        if OpenAIEmbeddings is None: raise RuntimeError("Установите langchain-openai")
        self.model = model; self._emb = OpenAIEmbeddings(model=model)
    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._emb.embed_documents(texts)
