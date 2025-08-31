from typing import List, Optional, Dict, Any

from neuroteacher.core.types import Doc
from neuroteacher.core.contracts import Embeddings, LLM
from neuroteacher.adapters.embeds.openai_embeds import OpenAIEmbeddingsAdapter
from neuroteacher.adapters.vectorstores.chroma_store import ChromaVectorStore
from neuroteacher.adapters.retrievers.dense_retriever import DenseRetriever
from neuroteacher.adapters.llm.openai_llm import OpenAIChatLLM
from neuroteacher.adapters.llm.gigachat_llm import GigaChatLLM
from neuroteacher.core.prompts import system_prompt_for


class RAGService:
    def __init__(
        self,
        persist_path: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small",
    ):
        self.persist_path = persist_path
        self.embeddings: Embeddings = OpenAIEmbeddingsAdapter(embedding_model)
        self.store = ChromaVectorStore(self.embeddings, persist_directory=self.persist_path)
        self.retriever = None

    def index(self, docs: List[Doc], k: int = 5) -> None:
        self.store.add(docs)
        self.retriever = DenseRetriever(self.store.as_retriever(k=k))

    def _retrieve(self, query: str):
        r = self.retriever
        if hasattr(r, "invoke"):
            return r.invoke(query)
        if hasattr(r, "get_relevant_documents"):
            return r.get_relevant_documents(query)
        raise AttributeError("Retriever has neither invoke nor get_relevant_documents")

    def answer(
        self,
        question: str,
        course: Optional[str] = None,
        vendor: str = "openai",
        model: str = "gpt-4o-mini",
    ) -> Dict[str, Any]:
        if self.retriever is None:
            raise RuntimeError("Индекс пуст. Сначала загрузите материалы.")

        docs = self._retrieve(question)
        context = "\n\n".join(getattr(d, "page_content", str(d)) for d in docs)
        sys_prompt = system_prompt_for(course)

        llm: LLM = (
            OpenAIChatLLM(name=model, temperature=0.2)
            if vendor == "openai"
            else GigaChatLLM(temperature=0.2)
        )

        out = llm.chat(
            [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": f"Вопрос: {question}\n\nКонтекст:\n{context}"},
            ]
        )

        return {
            "answer": out["content"],
            "usage": out.get("usage", {}),
            "sources": [getattr(d, "metadata", {}) for d in docs],
        }
