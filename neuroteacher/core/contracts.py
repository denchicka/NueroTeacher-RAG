class LLM:
    name: str
    temperature: float
    def chat(self, messages):
        raise NotImplementedError

class Embeddings:
    model: str
    def embed(self, texts):
        raise NotImplementedError

class Retriever:
    def invoke(self, query):
        raise NotImplementedError

class VectorStore:
    def add(self, docs):
        raise NotImplementedError
    def as_retriever(self, **kwargs):
        raise NotImplementedError
