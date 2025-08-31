from neuroteacher.core.contracts import Retriever

class DenseRetriever(Retriever):
    def __init__(self, lc_retriever):
        self._r = lc_retriever
    def invoke(self, query: str):
        if hasattr(self._r, "invoke"):
            return self._r.invoke(query)
        if hasattr(self._r, "get_relevant_documents"):
            return self._r.get_relevant_documents(query)
        raise AttributeError("Retriever has neither invoke nor get_relevant_documents")
    # Provide classic API too
    def get_relevant_documents(self, query: str):
        return self.invoke(query)
